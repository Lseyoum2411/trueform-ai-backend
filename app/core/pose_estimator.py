import cv2
import mediapipe as mp
import numpy as np
from typing import List, Dict, Tuple, Optional
import math


class PoseEstimator:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.mp_drawing = mp.solutions.drawing_utils
    
    def extract_frames(self, video_path: str, max_frames: Optional[int] = None) -> List[np.ndarray]:
        cap = cv2.VideoCapture(video_path)
        frames = []
        frame_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            frame_count += 1
            
            if max_frames and frame_count >= max_frames:
                break
        
        cap.release()
        return frames
    
    def get_landmarks(self, frame: np.ndarray) -> Optional[Dict[str, Tuple[float, float, float]]]:
        results = self.pose.process(frame)
        
        if not results.pose_landmarks:
            return None
        
        landmarks = {}
        landmark_names = [
            "nose", "left_eye_inner", "left_eye", "left_eye_outer",
            "right_eye_inner", "right_eye", "right_eye_outer",
            "left_ear", "right_ear", "mouth_left", "mouth_right",
            "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
            "left_wrist", "right_wrist", "left_pinky", "right_pinky",
            "left_index", "right_index", "left_thumb", "right_thumb",
            "left_hip", "right_hip", "left_knee", "right_knee",
            "left_ankle", "right_ankle", "left_heel", "right_heel",
            "left_foot_index", "right_foot_index",
        ]
        
        for i, landmark in enumerate(results.pose_landmarks.landmark):
            if i < len(landmark_names):
                landmarks[landmark_names[i]] = (
                    landmark.x,
                    landmark.y,
                    landmark.z,
                )
        
        return landmarks
    
    def calculate_angle(
        self,
        point1: Tuple[float, float, float],
        point2: Tuple[float, float, float],
        point3: Tuple[float, float, float],
    ) -> float:
        a = np.array([point1[0], point1[1]])
        b = np.array([point2[0], point2[1]])
        c = np.array([point3[0], point3[1]])
        
        vector_ba = a - b
        vector_bc = c - b
        
        dot_product = np.dot(vector_ba, vector_bc)
        magnitude_ba = np.linalg.norm(vector_ba)
        magnitude_bc = np.linalg.norm(vector_bc)
        
        if magnitude_ba == 0 or magnitude_bc == 0:
            return 0.0
        
        cos_angle = np.clip(dot_product / (magnitude_ba * magnitude_bc), -1.0, 1.0)
        angle_rad = np.arccos(cos_angle)
        angle_deg = np.degrees(angle_rad)
        
        return angle_deg
    
    def get_joint_angles(self, landmarks: Dict[str, Tuple[float, float, float]]) -> Dict[str, float]:
        angles = {}
        
        if all(k in landmarks for k in ["left_shoulder", "left_elbow", "left_wrist"]):
            angles["left_elbow"] = self.calculate_angle(
                landmarks["left_shoulder"],
                landmarks["left_elbow"],
                landmarks["left_wrist"],
            )
        
        if all(k in landmarks for k in ["right_shoulder", "right_elbow", "right_wrist"]):
            angles["right_elbow"] = self.calculate_angle(
                landmarks["right_shoulder"],
                landmarks["right_elbow"],
                landmarks["right_wrist"],
            )
        
        if all(k in landmarks for k in ["left_hip", "left_knee", "left_ankle"]):
            angles["left_knee"] = self.calculate_angle(
                landmarks["left_hip"],
                landmarks["left_knee"],
                landmarks["left_ankle"],
            )
        
        if all(k in landmarks for k in ["right_hip", "right_knee", "right_ankle"]):
            angles["right_knee"] = self.calculate_angle(
                landmarks["right_hip"],
                landmarks["right_knee"],
                landmarks["right_ankle"],
            )
        
        if all(k in landmarks for k in ["left_shoulder", "left_hip", "left_knee"]):
            angles["left_hip"] = self.calculate_angle(
                landmarks["left_shoulder"],
                landmarks["left_hip"],
                landmarks["left_knee"],
            )
        
        if all(k in landmarks for k in ["right_shoulder", "right_hip", "right_knee"]):
            angles["right_hip"] = self.calculate_angle(
                landmarks["right_shoulder"],
                landmarks["right_hip"],
                landmarks["right_knee"],
            )
        
        return angles
    
    def get_video_metadata(self, video_path: str) -> Dict:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {}
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        return {
            "fps": fps,
            "frame_count": frame_count,
            "width": width,
            "height": height,
            "duration": duration,
        }
    
    def process_video(self, video_path: str) -> List[Dict]:
        return self.analyze_video(video_path)
    
    def analyze_video(self, video_path: str) -> List[Dict]:
        frames = self.extract_frames(video_path)
        pose_data = []
        
        for frame in frames:
            landmarks = self.get_landmarks(frame)
            if landmarks:
                angles = self.get_joint_angles(landmarks)
                pose_data.append({
                    "landmarks": landmarks,
                    "angles": angles,
                })
        
        return pose_data
    
    def __del__(self):
        if hasattr(self, "pose"):
            self.pose.close()

