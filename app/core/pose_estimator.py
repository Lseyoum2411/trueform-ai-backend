import cv2
import mediapipe as mp
import numpy as np
from typing import List, Dict, Tuple, Optional
import math
import logging

logger = logging.getLogger(__name__)


class PoseEstimator:
    def __init__(self):
        # No MediaPipe initialization at class level - created per request
        pass
    
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
    
    def analyze_video(self, video_path: str, max_frames: Optional[int] = None, sample_rate: int = 1) -> List[Dict]:
        """
        Analyze video and extract pose data frame by frame.
        Creates MediaPipe Pose instance PER REQUEST using context manager.
        
        Args:
            video_path: Path to video file
            max_frames: Maximum number of frames to process (None = all frames)
            sample_rate: Process every Nth frame (1 = all frames, 2 = every other frame, etc.)
        
        Returns:
            List of pose data dictionaries with landmarks and angles
        """
        # Open video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Failed to open video file: {video_path}")
            return []
        
        pose_data = []
        frame_count = 0
        processed_count = 0
        
        try:
            # Get FPS to calculate max frames if needed (limit to ~60 seconds max at 30fps = 1800 frames)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            if not max_frames:
                # Default: limit to 1800 frames (60 seconds at 30fps) to prevent OOM
                max_frames = int(min(1800, fps * 60))
            
            # Create MediaPipe Pose instance PER REQUEST using context manager
            mp_pose = mp.solutions.pose
            with mp_pose.Pose(
                static_image_mode=False,
                model_complexity=0,  # Use 0 for faster processing
                enable_segmentation=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            ) as pose:
                
                # Process frames one by one
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Sample frames based on sample_rate
                    if frame_count % sample_rate == 0:
                        # Convert BGR to RGB before processing
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        
                        # Process frame with MediaPipe Pose
                        results = pose.process(frame_rgb)
                        
                        # Debug logging: log landmark value to verify real processing
                        if results.pose_landmarks:
                            lm = results.pose_landmarks.landmark
                            left_hip_x = lm[mp_pose.PoseLandmark.LEFT_HIP].x
                            logger.debug(f"DEBUG frame_{processed_count} hip_x: {left_hip_x:.4f}")
                            if processed_count < 3:  # Log first 3 frames
                                print(f"DEBUG frame_{processed_count} hip_x: {left_hip_x:.4f}")
                        
                        # Extract landmarks if detected
                        if results.pose_landmarks:
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
                            
                            # Calculate joint angles from landmarks
                            angles = self.get_joint_angles(landmarks)
                            pose_data.append({
                                "landmarks": landmarks,
                                "angles": angles,
                            })
                        
                        processed_count += 1
                        if processed_count >= max_frames:
                            break
                    
                    frame_count += 1
                    # Frame memory will be released automatically by Python GC
        
        finally:
            # Release video capture
            cap.release()
            del cap
        
        logger.info(f"Processed {processed_count} frames, extracted {len(pose_data)} frames with pose data")
        return pose_data
