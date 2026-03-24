#!/usr/bin/env python3
"""
test_aruco_window.py
====================
Live ArUco detection — camera 5 m, box markers 150 mm, shelf removed.
Run DIRECTLY in a graphical terminal:

    source ~/your_ws/install/setup.bash
    python3 test_aruco_window.py

FIXES vs previous:
  • findHomography crash fixed — strictly requires 4 points (OpenCV
    minimum for both RANSAC and LMEDS is 4, despite docs implying 3)
  • Rolling median of last 15 good H matrices — jitter-free
  • Multi-scale (1x + 2x) + 6 preprocessing variants + 3 param sets
  • Slot 1 (ID 11) z_gt updated to 1.280 m to match SDF
"""

import sys, os, threading, time
from collections import deque

print("="*60)
print("STEP 1  opencv-python")
print("="*60)
try:
    import cv2, numpy as np
    print(f"  OK  cv2={cv2.__version__}  numpy={np.__version__}")
except ImportError as e:
    print(f"  FAIL: {e}"); sys.exit(1)

print("\nSTEP 2  ArUco detector")
print("="*60)
try:
    _adict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

    def _make_params(min_p, tc, tmax):
        p = cv2.aruco.DetectorParameters()
        for attr, val in {
            "cornerRefinementMethod":               getattr(cv2.aruco,"CORNER_REFINE_SUBPIX",2),
            "cornerRefinementWinSize":              5,
            "cornerRefinementMaxIterations":        50,
            "cornerRefinementMinAccuracy":          0.05,
            "minMarkerPerimeterRate":               min_p,
            "maxMarkerPerimeterRate":               4.0,
            "polygonalApproxAccuracyRate":          0.10,
            "errorCorrectionRate":                  0.90,
            "minDistanceToBorder":                  1,
            "adaptiveThreshWinSizeMin":             3,
            "adaptiveThreshWinSizeMax":             tmax,
            "adaptiveThreshWinSizeStep":            4,
            "adaptiveThreshConstant":               tc,
            "perspectiveRemovePixelPerCell":        4,
            "perspectiveRemoveIgnoredMarginPerCell":0.13,
        }.items():
            try: setattr(p, attr, val)
            except (AttributeError, TypeError): pass
        return p

    _params_list = [
        _make_params(0.004, 7.0,  35),
        _make_params(0.002, 5.0,  51),
        _make_params(0.002, 11.0, 23),
    ]

    _NEW_API = False
    try:
        _detectors = [cv2.aruco.ArucoDetector(_adict, p) for p in _params_list]
        _NEW_API   = True
        print(f"  new API  ({len(_detectors)} param sets)")
    except AttributeError:
        _detectors = [(_adict, p) for p in _params_list]
        print(f"  legacy   ({len(_detectors)} param sets)")
except Exception as e:
    print(f"  FAIL: {e}"); sys.exit(1)

def _detect_one(det, gray):
    if _NEW_API: return det.detectMarkers(gray)
    d, p = det;  return cv2.aruco.detectMarkers(gray, d, parameters=p)

print("\nSTEP 3  $DISPLAY")
print("="*60)
os.environ.setdefault("QT_QPA_PLATFORM","xcb")
print(f"  DISPLAY={os.environ.get('DISPLAY','NOT SET')}")

print("\nSTEP 4  cv2 window")
print("="*60)
try:
    splash = np.zeros((180,700,3),dtype=np.uint8)
    cv2.putText(splash,"cv2 OK",(20,100),cv2.FONT_HERSHEY_SIMPLEX,0.9,(0,255,0),2)
    cv2.namedWindow("Dexter ArUco",cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Dexter ArUco",960,540)
    cv2.imshow("Dexter ArUco",splash)
    cv2.waitKey(1)
    print("  Window OK")
except Exception as e:
    print(f"  FAIL: {e}"); sys.exit(1)

print("\nSTEP 5  ROS2 (no cv_bridge)")
print("="*60)

def ros_to_bgr(msg):
    enc=msg.encoding.lower().replace("-","")
    h,w=msg.height,msg.width
    raw=np.frombuffer(bytes(msg.data),dtype=np.uint8)
    if enc in("bgr8","8uc3"):  return raw.reshape(h,w,3).copy()
    if enc=="rgb8":            return cv2.cvtColor(raw.reshape(h,w,3),cv2.COLOR_RGB2BGR)
    if enc in("bgra8","8uc4"):return cv2.cvtColor(raw.reshape(h,w,4),cv2.COLOR_BGRA2BGR)
    if enc=="rgba8":           return cv2.cvtColor(raw.reshape(h,w,4),cv2.COLOR_RGBA2BGR)
    if enc in("mono8","8uc1"):return cv2.cvtColor(raw.reshape(h,w),  cv2.COLOR_GRAY2BGR)
    try:    return raw.reshape(h,w,3).copy()
    except: raise ValueError(f"Unsupported: {msg.encoding}")

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
import json
print("  rclpy OK  |  cv_bridge NOT used")

# ── Constants ──────────────────────────────────────────────────────────────────
CAM_X_MM=1000.0; CAM_Y_MM=0.0; CAM_Z_MM=5000.0
BOX_Z_MM =1218.0
BOX1_Z_MM=1280.0   # slot 1 marker raised 6 cm in SDF
GRIP_Z_MM= 850.0
T_BOX  =(CAM_Z_MM-BOX_Z_MM) /CAM_Z_MM   # 0.7564
T_BOX1 =(CAM_Z_MM-BOX1_Z_MM)/CAM_Z_MM   # 0.7440
T_GRIP =(CAM_Z_MM-GRIP_Z_MM)/CAM_Z_MM   # 0.8300

REF_WORLD={1:[-600.,-1900.],2:[2000.,-1900.],3:[-600.,+1900.],4:[2000.,+1900.]}
# ground-truth world positions per slot (mm) — slot 1 z matches raised marker
SLOT_GT={0:(1048.,-642.),1:(1209.,-220.),2:(1209.,+220.),3:(1048.,+642.)}
# parallax t per slot
SLOT_T={0:T_BOX,1:T_BOX1,2:T_BOX,3:T_BOX}
BOX_TO_SLOT={10:0,11:1,12:2,13:3}

MARKER_META={
    1:("REF-FL",( 20,180,255)),2:("REF-BR",( 20,180,255)),
    3:("REF-FR",( 20,180,255)),4:("REF-BL",( 20,180,255)),
    5:("ARM-BASE",(255,120,30)),
    10:("SLOT-0",(0,220,80)),11:("SLOT-1",(0,220,80)),
    12:("SLOT-2",(0,220,80)),13:("SLOT-3",(0,220,80)),
    21:("GRIPPER",(0,80,255)),
}

def _preprocess(gray):
    variants=[]
    norm =cv2.normalize(gray,None,0,255,cv2.NORM_MINMAX); variants.append(norm)
    clahe=cv2.createCLAHE(clipLimit=3.5,tileGridSize=(8,8)).apply(norm); variants.append(clahe)
    lut  =(np.arange(256,dtype=np.float32)/255.0)**(1./1.6)*255
    variants.append(cv2.LUT(clahe,lut.astype(np.uint8)))
    k=np.array([[-1,-1,-1],[-1,9,-1],[-1,-1,-1]])
    variants.append(cv2.filter2D(clahe,-1,k))
    variants.append(cv2.bilateralFilter(norm,9,75,75))
    _,otsu=cv2.threshold(clahe,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    variants.append(otsu)
    return variants

def _detect_all(gray):
    best={}
    for sc in [1.0,2.0]:
        g=gray if sc==1.0 else cv2.resize(gray,None,fx=sc,fy=sc,interpolation=cv2.INTER_LINEAR)
        for proc in _preprocess(g):
            for det in _detectors:
                try: corners,ids,_=_detect_one(det,proc)
                except Exception: continue
                if ids is None: continue
                for i,mid in enumerate(ids.flatten()):
                    c=(corners[i][0]/sc).reshape(1,4,2)
                    area=cv2.contourArea(c[0])
                    if mid not in best or area>best[mid][1]:
                        best[mid]=(c,area)
    return best

# ── Homography — STRICTLY 4+ points ───────────────────────────────────────────
# OpenCV findHomography requires minimum 4 point correspondences regardless
# of method (RANSAC or LMEDS). Using fewer crashes with error -28.
_H_history=deque(maxlen=15)
_H_stable=None

def _update_H(pix_pts, world_pts):
    global _H_stable
    if len(pix_pts) < 4:          # ← strict guard, no LMEDS fallback
        return                     #   just keep last stable H
    H,_=cv2.findHomography(
        np.array(pix_pts,np.float32),
        np.array(world_pts,np.float32),
        cv2.RANSAC, 5.0)
    if H is None: return
    _H_history.append(H)
    _H_stable=np.median(np.array(list(_H_history)),axis=0) if len(_H_history)>=3 else H

def _px2world(px,py,t):
    if _H_stable is None: return None,None
    w=cv2.perspectiveTransform(np.array([[[float(px),float(py)]]],np.float32),_H_stable)
    xf,yf=float(w[0,0,0]),float(w[0,0,1])
    return CAM_X_MM+t*(xf-CAM_X_MM), CAM_Y_MM+t*(yf-CAM_Y_MM)

def _world2px(xw,yw):
    if _H_stable is None: return None
    Hi=np.linalg.inv(_H_stable)
    p=cv2.perspectiveTransform(np.array([[[float(xw),float(yw)]]],np.float32),Hi)
    return (int(p[0,0,0]),int(p[0,0,1]))

# ── Shared state ───────────────────────────────────────────────────────────────
_latest=None; _frame_lock=threading.Lock()
_count=0; _ids_now=[]; _slot_meas={}; _grip_meas=None

class ArucoNode(Node):
    def __init__(self):
        super().__init__("aruco_test")
        self.create_subscription(Image,"/camera/image_raw",self._cb,1)
        # Publisher for box poses - used by visual_servo_node
        self.box_poses_pub = self.create_publisher(String, "/inventory/box_poses", 10)
        self.get_logger().info("Subscribed /camera/image_raw, publishing to /inventory/box_poses")

    def _cb(self,msg):
        global _latest,_count,_ids_now,_slot_meas,_grip_meas
        try: frame=ros_to_bgr(msg)
        except Exception as e:
            self.get_logger().warn(f"decode:{e}"); return

        _count+=1
        gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        best=_detect_all(gray)
        vis=frame.copy(); det=[]

        # collect refs (only attempt H if we have exactly 4)
        ref_pix,ref_wld=[],[]
        for mid,(ci,_) in best.items():
            if int(mid) in REF_WORLD:
                ref_pix.append(ci[0].mean(axis=0))
                ref_wld.append(REF_WORLD[int(mid)])
        _update_H(ref_pix,ref_wld)

        # expected grid overlay
        if _H_stable is not None:
            try:
                Hi=np.linalg.inv(_H_stable)
                pts=np.array([REF_WORLD[1],REF_WORLD[2],REF_WORLD[4],REF_WORLD[3]],np.float32)
                proj=cv2.perspectiveTransform(pts.reshape(1,-1,2),Hi)[0].astype(int)
                cv2.polylines(vis,[proj.reshape(-1,1,2)],True,(60,60,180),2)
                for s,(sx,sy) in SLOT_GT.items():
                    px=_world2px(sx,sy)
                    if px:
                        cv2.drawMarker(vis,px,(0,160,60),cv2.MARKER_CROSS,20,2)
                        cv2.putText(vis,f"EXP{s}",(px[0]+5,px[1]-5),
                                    cv2.FONT_HERSHEY_SIMPLEX,0.38,(0,160,60),1)
            except Exception: pass

        if best:
            c_list=[v[0] for v in best.values()]
            id_arr=np.array([[k] for k in best.keys()],dtype=np.int32)
            cv2.aruco.drawDetectedMarkers(vis,c_list,id_arr)

        slot_m={}; grip_m=None

        for mid,(ci,_) in best.items():
            ctr=ci[0].mean(axis=0).astype(int)
            ix,iy=int(ctr[0]),int(ctr[1])
            label,color=MARKER_META.get(int(mid),(f"ID{mid}",(200,200,200)))
            det.append(int(mid))
            cv2.circle(vis,(ix,iy),12,color,-1)
            cv2.circle(vis,(ix,iy),16,color,2)
            cv2.putText(vis,label,(ix+18,iy-10),cv2.FONT_HERSHEY_SIMPLEX,0.56,color,2)

            if int(mid) in BOX_TO_SLOT and _H_stable is not None:
                s=BOX_TO_SLOT[int(mid)]
                t=SLOT_T[s]
                xw,yw=_px2world(ix,iy,t)
                if xw is not None:
                    slot_m[s]=(round(xw/1000,3),round(yw/1000,3))
                    ex,ey=SLOT_GT[s]
                    err=((xw-ex)**2+(yw-ey)**2)**0.5
                    cv2.putText(vis,f"({xw/1000:.3f},{yw/1000:.3f}) e={err:.0f}mm",
                                (ix+18,iy+14),cv2.FONT_HERSHEY_SIMPLEX,0.40,(0,200,70),1)

            if int(mid)==21 and _H_stable is not None:
                xw,yw=_px2world(ix,iy,T_GRIP)
                if xw is not None:
                    grip_m=(round(xw/1000,3),round(yw/1000,3))
                    cv2.circle(vis,(ix,iy),28,(0,80,255),3)
                    cv2.putText(vis,f"GRIP({xw/1000:.3f},{yw/1000:.3f})",
                                (ix+18,iy+18),cv2.FONT_HERSHEY_SIMPLEX,0.50,(0,80,255),2)

        _ids_now=sorted(det); _slot_meas=slot_m; _grip_meas=grip_m

        # ── Publish box poses for visual_servo_node ──
        # Format: {"0": {"x": 1.048, "y": -0.642, "z": 1.156, "detected": true}, ...}
        box_poses = {}
        for s in range(4):
            if s in slot_m:
                x_m, y_m = slot_m[s]
                box_poses[str(s)] = {
                    "x": x_m,
                    "y": y_m,
                    "z": 1.156,  # Box height
                    "detected": True
                }
            else:
                # Fall back to ground truth if not detected
                gt_x, gt_y = SLOT_GT[s]
                box_poses[str(s)] = {
                    "x": gt_x / 1000.0,
                    "y": gt_y / 1000.0,
                    "z": 1.156,
                    "detected": False
                }
        
        # Publish
        msg = String()
        msg.data = json.dumps(box_poses)
        self.box_poses_pub.publish(msg)

        refs_seen=sum(1 for m in det if m in REF_WORLD)
        h_ok=_H_stable is not None
        missing=[s for s in range(4) if (s+10) not in det]

        ov=vis.copy()
        cv2.rectangle(ov,(0,0),(720,130),(8,8,8),-1)
        cv2.addWeighted(ov,0.72,vis,0.28,0,vis)

        hom_txt=(f"LOCKED ({refs_seen}/4)" if h_ok
                 else f"need {max(0,4-refs_seen)} more ref(s) ({refs_seen}/4 seen)")
        cv2.putText(vis,f"Frame {_count}  Homography: {hom_txt}",
                    (8,22),cv2.FONT_HERSHEY_SIMPLEX,0.54,
                    (0,220,0) if h_ok else (0,120,255),1)
        cv2.putText(vis,f"IDs: {_ids_now}",
                    (8,46),cv2.FONT_HERSHEY_SIMPLEX,0.52,(200,200,200),1)
        cv2.putText(vis,f"Slots: {slot_m}  Missing(FK):{missing}",
                    (8,70),cv2.FONT_HERSHEY_SIMPLEX,0.47,(0,220,80),1)
        cv2.putText(vis,f"Gripper:{grip_m if grip_m else 'not visible'}",
                    (8,94),cv2.FONT_HERSHEY_SIMPLEX,0.47,
                    (0,80,255) if grip_m else (80,80,80),1)
        cv2.putText(vis,"Q/Esc=quit",(8,116),cv2.FONT_HERSHEY_SIMPLEX,0.40,(80,80,80),1)

        with _frame_lock:
            _latest=cv2.resize(vis,(960,540))

# ── Start ──────────────────────────────────────────────────────────────────────
rclpy.init()
node=ArucoNode()
spin_t=threading.Thread(target=rclpy.spin,args=(node,),daemon=True)
spin_t.start()
print("  Spinning in background thread")
print("\n"+"="*60)
print("  findHomography: strictly 4+ refs (crash fixed)")
print("  2× upscale + 6 prepros + 3 param sets = 36 passes/frame")
print("  Slot 1 ArUco raised 6 cm in SDF (clears arm body)")
print("  Q / Esc to quit")
print("="*60+"\n")

last_log=0.; no_frame=True

while rclpy.ok() and spin_t.is_alive():
    with _frame_lock:
        frame=_latest.copy() if _latest is not None else None

    if frame is not None:
        if no_frame:
            print(f"  ✓ First frame {frame.shape[1]}x{frame.shape[0]}")
            no_frame=False
        cv2.imshow("Dexter ArUco",frame)
    else:
        w=np.zeros((540,960,3),dtype=np.uint8)
        d="."*(int(time.time()*2)%4)
        cv2.putText(w,f"Waiting for /camera/image_raw{d}",
                    (140,260),cv2.FONT_HERSHEY_SIMPLEX,1.0,(60,60,60),2)
        cv2.imshow("Dexter ArUco",w)

    now=time.time()
    if now-last_log>2.0 and not no_frame:
        last_log=now
        refs=sum(1 for m in _ids_now if m in REF_WORLD)
        print(f"  f={_count:5d}  refs={refs}/4  hom={'OK' if _H_stable is not None else 'NO'}  IDs={_ids_now}")
        if _slot_meas:
            for s,(x,y) in sorted(_slot_meas.items()):
                ex,ey=SLOT_GT[s]
                err=((x*1000-ex)**2+(y*1000-ey)**2)**0.5
                print(f"         slot{s}:({x:.3f},{y:.3f})m  exp:({ex/1000:.3f},{ey/1000:.3f})m  err={err:.0f}mm")
        if _grip_meas: print(f"         grip:{_grip_meas}")

    key=cv2.waitKey(30)&0xFF
    if key in(ord('q'),27): break

cv2.destroyAllWindows()
node.destroy_node()
try: rclpy.shutdown()
except: pass
print(f"\n  Frames:{_count}  IDs:{_ids_now}")
