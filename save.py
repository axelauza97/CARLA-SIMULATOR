from os import listdir
from os.path import isfile, join
import cv2

def saveVideo(files,folder,name):	
	images=[]
	for file in files:
		images.append(cv2.imread(folder+file,1))
	print "Proccessing "+ name +" images"
	fourcc = cv2.VideoWriter_fourcc(*'XVID')
	#8 2 videos mitad
	outI = cv2.VideoWriter(name+'.avi',fourcc, 10, (1200,700))
	while(len(images)!=0 ):
	    outI.write(images.pop())
	outI.release()

filesI = [f for f in listdir('outI/') if isfile(join('outI/', f))]
filesD = [f for f in listdir('outD/') if isfile(join('outD/', f))]
filesF = [f for f in listdir('outF/') if isfile(join('outF/', f))]
filesA = [f for f in listdir('outA/') if isfile(join('outA/', f))]


filesI.sort(reverse = True)
filesD.sort(reverse = True)
filesF.sort(reverse = True)
filesA.sort(reverse = True)

saveVideo(filesI,'outI/','outI')
saveVideo(filesD,'outD/','outD')
saveVideo(filesF,'outF/','outF')
saveVideo(filesA,'outA/','outA')
