import cv2 as cv
import numpy as np
import os
import time
from time import sleep
import keyboard
import pyautogui, sys
from vision import Vision
from hsvfilter import HsvFilter
import random
import socket #for keyboard/mouse app connection
import win32api #for alerts
#load model & vision class
#bs cascade_fishbait = cv.CascadeClassifier('output/cascade.xml')
vision_fishbait = Vision('needle.jpg')
hsv_filter = HsvFilter(21, 38, 155, 130, 190, 255, 0, 0, 0, 0)


sm = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    sm.connect(("127.0.0.1", 49596))
    sk.connect(("127.0.0.1", 49595))
except Exception as e:
    win32api.MessageBox(0, 'error during connection to the mouse/keyboard input app', 'Error')
    sm.close()
    sk.close()

sm.send("click,LD|".encode())
sleep(0.1)
sm.send("click,LU|".encode())
def detect():
        #print("enter detect()")
        fishbait_loc = np.array([])
        timer=0
        bufftimer=0
        while (True):
                #print(timer)
                startTime=time.time()
                #screen capture
                screenshot = pyautogui.screenshot(region=(0,0, 1920, 1080))
                screenshot = np.array(screenshot)
                #image preprocessing
                processed_image = vision_fishbait.apply_hsv_filter(screenshot, hsv_filter)
                #object detection
                rectangles = vision_fishbait.find(processed_image, 0.4)
                #print(fishbait_loc.size)
                #if fishbait_loc.size!=0:
                        #if rectangles.size!=0:
                                #print("current pos:"+str(rectangles[0, 1])+"   first pos:"+str(fishbait_loc[0, 1]))
                if fishbait_loc.size==0 and rectangles.size!=0 :
                        fishbait_loc=rectangles
                elif fishbait_loc.size!=0 and (rectangles.size==0 or rectangles[0, 1]-9>fishbait_loc[0, 1]):
                        #print("exit detect() by elif")
                        timer=0
                        if bufftimer >=1800:
                                bufftimer=0
                                buffup()
                        else:
                                move_mouse(fishbait_loc)
                        fishbait_loc = np.array([])
                #print(rectangles)
                #output_image = vision_fishbait.draw_rectangles(screenshot, rectangles)

                key = cv.waitKey(1)
                #cv.imshow('preview', output_image)
                if keyboard.is_pressed('p'):
                        cv.destroyAllWindows()
                        break
                timer+=(time.time()-startTime)
                bufftimer+=(time.time()-startTime)
                if timer >= 22:
                        fishbait_loc = np.array([])
                        timer=0
                        next_fishing()
def buffup():
    sk.send("0x03,d|0x03,u|".encode())
    sleep(3)
    return
def start_fishing():
    sleep(1)
    #SEND KEYBOARD BUTTON 1
    sk.send("0x02,d|0x02,u|".encode())
    #SMALL DELAY
    sleep(2)
    #print("return from start_fishing()")
    return
def move_mouse(rect):
    curpos=pyautogui.position()
    x_min=rect[0, 0]
    x_max=x_min+rect[0, 2]
    y_min=rect[0, 1]
    y_max=y_min+rect[0, 3]
    x_target=int(rect[0, 0]+rect[0, 2]/2)
    y_target=int(rect[0, 1]+rect[0, 3]/2)
    #print(curpos)
    #print(rect)
    while curpos[0]<x_min or curpos[0]>x_max or curpos[1]<y_min or curpos[1]>y_max:
        #print("while in move_mouse()")
        #print("curpos[0]|x_min|x_max  -   curpos[1]|y_min|y_max")
        #print(str(curpos[0])+"|"+str(x_min)+"|"+str(x_max)+"  -  "+str(curpos[1])+"|"+str(y_min)+"|"+str(y_max))
        myarr = bezier(curpos[0],curpos[1],x_target,y_target)
        for i in range(1,500):
            data=str(int(myarr[i, 0]-myarr[i-1, 0]))+","+str(int(-myarr[i, 1]+myarr[i-1, 1]))+"|"
            sm.send(data.encode())
            sleep(0.002)
        curpos=pyautogui.position()
    sleep(random.random())
    sm.send("click,RD|click,RU|".encode())
    #print("enter() next_fishing() from move_mouse()")
    return next_fishing()
def next_fishing():
    sleep(random.random())
    #print("start_fishing enter from next_fishing()")
    return start_fishing()
def bezier(cur_x, cur_y, tgt_x, tgt_y):
    sign=bool(random.getrandbits(1))
    reverse=bool(random.getrandbits(1))
    overshoot=random.uniform(7, 30)
    direction1=0.4
    direction2=random.uniform(1, 6)
    direction3=random.uniform(1, 6)
    direction4=tgt_x
    direction5=tgt_y
    if sign==True:
        overshoot=-random.uniform(7, 30)
        direction1=1.25
        direction4=cur_x
        direction5=cur_y
    if reverse==True:        
        direction2=-random.uniform(4, 7)
        direction3=-random.uniform(0, 3)
    
    randfactor=round(random.uniform(0.8, 1.2),2)
    p1xP=abs(direction4+((tgt_x-cur_x))*direction1/direction2)+overshoot
    p1yP=abs(direction5+((tgt_y-cur_y))*direction1/direction2)+overshoot
    p2xP=abs(direction4-(((tgt_x-cur_x))*direction1)/direction3)-overshoot
    p2yP=abs(direction5-(((tgt_y-cur_y))*direction1)/direction3)-overshoot

    mvmentsArr=np.zeros(shape=(500,2))
    mv_single=1/500
    mv=1/500
    i=1
    scanpos=pyautogui.position()
    mvmentsArr[0]=[scanpos[0], scanpos[1]]
    x_left=0
    y_left=0
    while mv<1:
        one_minus_mv=1-mv
        a=one_minus_mv**3
        b=3*((one_minus_mv)**2)*mv
        c=3*(one_minus_mv)*(mv**2)
        d=(mv**3)
        
        x=(a*cur_x+b*p1xP+c*p2xP+d*tgt_x)
        y=(a*cur_y+b*p1yP+c*p2yP+d*tgt_y)
        x_left=x%1
        y_left=y%1
        x-=x_left
        y-=y_left
        if x_left>=1:
            x+=1
            x_left-=1
        elif y_left>=1:
            y+=1
            y_left-=1
        mvmentsArr[i]=[x, y]
        mv+=mv_single
        i+=1
    return(mvmentsArr)

print("start fishing from bottom of the script")
start_fishing()
detect()

#0x03,d|     0x03,u|   (2é~) key to send every now and then to reactivate fishing buff
