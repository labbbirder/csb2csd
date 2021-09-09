#encoding:utf8
import argparse
from convert import dealWithCsbFile as copy_csb
from shutil import copyfile
import json
import os
import random
import re
import tempfile
import logging
import colorlog
import plistlib

logger = logging.getLogger('logger_name')

# 输出到控制台
console_handler = logging.StreamHandler()

console_formatter = colorlog.ColoredFormatter(
    fmt='%(log_color)s[%(levelname)s] : %(message)s',
    log_colors= {
	    'DEBUG': 'white',  # cyan white
	    'INFO': 'green',
	    'WARNING': 'yellow',
	    'ERROR': 'red',
	    'CRITICAL': 'bold_red',
	}
)
logger.setLevel(logging.DEBUG)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(console_formatter)

if not logger.handlers:
	logger.addHandler(console_handler)

console_handler.close()

blank_image_path = os.path.join(os.path.dirname(__file__),"blank.png")
dependence = {}
missing = {}
category = {}


plistlib.load = getattr(plistlib,"load",plistlib.readPlist)
plistlib.dump = getattr(plistlib,"dump",plistlib.writePlist)

# avoid too much identical operations
class DelayedTasks:
	def __init__(self,pool_size):
		self.pool_size = pool_size
		self.pool = {}
		self.worker = {}
	def __call__(self,func):
		self.worker[func.__name__] = func
		self.pool[func.__name__] = self.pool.get(func.__name__,set())
		fpool = self.pool[func.__name__]
		def inner(*args):
			fpool.add(args)
			if len(fpool)>=self.pool_size:
				self.dump(func.__name__)
			return
		return inner
	def __del__(self):
		self.dump_all()
	def dump(self,name):
		cnt = len(self.pool[name])
		if cnt==0:
			return
		logger.debug("dump %d tasks with %s"%(cnt,name))
		for args in self.pool[name]:
			self.worker[name](*args)
		self.pool[name].clear()
	def dump_all(self):
		for name in self.worker.keys():
			self.dump(name)

delayed = DelayedTasks(64)






def prepare_folder(dst):
	if not os.path.exists(os.path.dirname(dst)):
		os.makedirs(os.path.dirname(dst))



def copy_plist(src,dst):
	srcdir = os.path.dirname(src)
	dstdir = os.path.dirname(dst)
	try:
		data = plistlib.load(open(src,"rb"))
		img = data["metadata"]["realTextureFileName"]
		if os.path.splitext(img)[1] in [".png",".jpg",".gif",".bmp"]:
			copyfile(
				os.path.join(srcdir,img),
				os.path.join(dstdir,img))
		else:
			fn = os.path.splitext(img)[0]
			data["metadata"]["realTextureFileName"]=fn+".png"
			data["metadata"]["textureFileName"]=fn+".png"

			code = os.system("TexturePacker --texture-format png --sheet %s.png --data %s %s --algorithm Basic --png-opt-level 0 --no-trim --dither-none-nn --extrude 0 --disable-auto-alias"
				%(os.path.join(dstdir,fn),tempfile.mktemp(),os.path.join(srcdir,img)))
			if 0!=code:
				logger.warning("TexturePacker execute failed.")
			else:
				logger.debug("image format transformed.")
		plistlib.dump(data,open(dst,"wb"))
		logger.debug("copy plist '%s' with '%s'"%(os.path.basename(dst),img))
	except:
		#may be particle file
		copyfile(src,dst)



@delayed
def copy_res(src,dst):
	if os.path.isdir(src):
		return
	prepare_folder(dst)

	if src.endswith(".plist"):
		copy_plist(src,dst)
	elif src.endswith(".fnt"):
		#TODO: fnt file copy
		copyfile(src,dst)
	elif src.endswith(".csb"):
		pass
	else:
		copyfile(src,dst)


def map_fields(fields):
	if fields[2].endswith(".csb"):
		fields[2] = fields[2][:-3]+"csd"
		return tuple(fields)
	else:
		return tuple(fields)



def ReferenceCallback(args):
	def _search_resource(src,search_path):
		rp = None
		for root in search_path:
			fp = os.path.join(root,src)
			if os.path.exists(fp):
				rp = fp
				break
		return rp

	def _getRefOutPath(refPath,islong=False):
		if args.category:
			return os.path.join(args.output,category[refPath]) if islong else category[refPath]
		else:
			return os.path.join(args.output,refPath) if islong else refPath

	def _refill(refPath,fields):
		if args.refill=="cocos":
			fields = (fields[0],"Default","Default/Sprite.png","")
		elif args.refill=="blank":
			if refPath.endswith(".plist"):
				refPath += "/blank_in_plist.png"
			copy_res(blank_image_path,_getRefOutPath(refPath,True))
			fields = (fields[0],"Normal",_getRefOutPath(refPath),"")
		elif args.refill=="drop":
			fields = (fields[0],"","","")
		elif args.refill=="keep":
			pass
		return fields
		# copy_res(rp,os.path.join(args.output,src))
	def _onRef(csdPath,refPath,fields):
		srcfile = os.path.relpath(csdPath,args.output)
		depfile = refPath

		dependence[srcfile] = dependence.get(srcfile,[])
		if not depfile in dependence[srcfile]:
			dependence[srcfile].append(depfile)

		fpath = _search_resource(refPath,[args.input]+(args.search_path or []))

		# if not os.path.exists(os.path.join(args.output,depfile)):
		if fpath:
			if args.copy!="no":
				copy_res(fpath,_getRefOutPath(refPath,True))
			fields = map_fields([_getRefOutPath(f) if f==refPath else f for f in fields])
		else:
			logger.debug("deal with missing reference '%s'"%depfile)

			missing[srcfile] = missing.get(srcfile,[])
			if not depfile in missing[srcfile]:
				missing[srcfile].append(depfile)

			fields = _refill(refPath,fields)

		return '  <%s Type="%s" Path="%s" Plist="%s" />\n'%fields
	return _onRef




def NameCallback(args):
	def _onName(name):
		if args.name_fix and not re.match(r'^[_a-zA-Z]+\w*$',name):
			newname = 'name_%x'%int(random.random()*0x100000000)
			logger.debug("rename node: '%s'->'%s'"%(name,newname))
			name = newname
		return 'Name="%s" '%name
	return _onName



def main():
	parser = argparse.ArgumentParser(description="反编译cocostudio的csb文件")
	parser.add_argument("-d","--output-dependency",action="store_true",
		help="output information of dependencies to dependence.json")
	parser.add_argument("-m","--output-missing-reference",action="store_true",
		help="output information of missing references to missing.json")
	parser.add_argument("-r","--refill",
		type=str,choices=["keep","cocos","blank","drop"],default="pass",
		help="what to do with the missing references, \
		especially the image file. 'keep' is to let it be, \
		'cocos' is to replace it with default resource of cocostudio, \
		'blank' is to replace it with a transparent image. \
		default is 'keep'.")
	parser.add_argument("-c","--copy",
		type=str,choices=["all","ref","no"],default="all",
		help="which files in folder should be copied besides csd. \
		'all' means whatever, \
		'ref' means only those referenced, \
		'no' means csd only. \
		default is 'all'.")
	parser.add_argument("-s","--search-path",nargs="+",
		help="additional paths to search the missing references, \
		only effects in 'ref' mode of copy option.")
	parser.add_argument("-n","--name-fix",action="store_true",
		help="rename the nodes whose name is illegal in lua.")
	parser.add_argument("-g","--category",action="store_true",
		help="category referenced files under a specific folder by csb.")
	# parser.add_argument("--relpath",type=str,default="",
	# 	help="relative path of references, usually not needed.")
	parser.add_argument("input",help="输入的csb文件或目录")
	parser.add_argument("output",help="输出目录")
	args = parser.parse_args()


	dependence.clear()
	missing.clear()
	category.clear()

	def main(args):

		# print(args)
		if(os.path.isdir(args.input)):
			# treat input as a folder
			for root,dirs,files in os.walk(args.input):

				for fp in [os.path.join(root,f) for f in files]:
					sp = os.path.relpath(fp,args.input)
					outfile = os.path.join(args.output,sp)

					if fp.endswith(".csb"):
						prepare_folder(outfile)
						outfile = os.path.splitext(outfile)[0]+".csd"
						copy_csb(
							fp,outfile,
							onRef = ReferenceCallback(args),
							onName = NameCallback(args),
							logger=logger)
						continue
					
					if args.copy=="all": 
						copy_res(fp,outfile)
			
			logger.info("translation completed! check your artifacts under %s"%os.path.realpath(args.output))
		
		else:
			if not os.path.isdir(args.output):
				logger.error("err: outpath is not a dir")
				return
			fn = os.path.basename(os.path.splitext(args.output)[0])+".csd"
			# treat input as a single file
			copy_csb(args.input,os.path.join(args.output,fn),logger=logger)

		# clear all tasks remained
		delayed.dump_all()

		if args.output_dependency:
			with open(os.path.join(args.output,"dependence.json"),"w+") as f:
				f.write(json.dumps(dependence,indent=4))
		if args.output_missing_reference:
			with open(os.path.join(args.output,"missing.json"),"w+") as f:
				f.write(json.dumps(missing,indent=4))

	if args.category:
		p_copy = args.copy
		args.output_dependency = True
		args.copy = "no"
		args.category = False
		main(args)
		for csd,dependencies in dependence.items():
			for depfile in dependencies:
				category[depfile] = category.get(depfile,set())
				category[depfile].add(csd)
		for depfile,owners in category.items():
			dst = os.path.splitext(owners.pop())[0] if len(owners)==1 else "common"
			dst = os.path.join("dependencies",dst,depfile)
			category[depfile] = dst
		args.category = True 
		args.copy = p_copy
		main(args)
	else:
		main(args)
	# end main()




if __name__ == '__main__':
	main()