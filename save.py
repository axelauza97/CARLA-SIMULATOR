from os import listdir
from os.path import isfile, join
import cv2

filesI = [f for f in listdir('outI/') if isfile(join('outI/', f))]
filesD = [f for f in listdir('outD/') if isfile(join('outD/', f))]
filesF = [f for f in listdir('outF/') if isfile(join('outF/', f))]
filesA = [f for f in listdir('outA/') if isfile(join('outA/', f))]


filesI.sort(reverse = True)
filesD.sort(reverse = True)
filesF.sort(reverse = True)
filesA.sort(reverse = True)

imagesI=[]
imagesD=[]
imagesF=[]
imagesA=[]

for file in filesI:
    imagesI.append(cv2.imread('outI/'+file,1))
print "PROCESSING left images"
fourcc = cv2.VideoWriter_fourcc(*'XVID')
#8 2 videos mitad
outI = cv2.VideoWriter('outputI.avi',fourcc, 10, (1200,700))
while(len(imagesI)!=0 ):
    outI.write(imagesI.pop())
outI.release()

