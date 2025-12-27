from abc import ABC
from typing import List, Dict
import numpy as np
from app.core.analyzers.base import BaseAnalyzer
from app.models.analysis import MetricScore, FeedbackItem


class BaseLiftAnalyzer(BaseAnalyzer, ABC):
    def analyze_depth(self, landmarks_list: List[Dict], ideal_depth: float) -> tuple[float, MetricScore, List[FeedbackItem]]:
        if not landmarks_list:
            return 50.0, self.create_metric("depth", 50.0), []
        
        depths = []
        for landmarks in landmarks_list:
            if "left_hip" in landmarks and "left_knee" in landmarks and "left_ankle" in landmarks:
                hip_y = landmarks["left_hip"][1]
                knee_y = landmarks["left_knee"][1]
                ankle_y = landmarks["left_ankle"][1]
                
                leg_length = abs(hip_y - ankle_y)
                if leg_length > 0:
                    depth_ratio = abs(hip_y - knee_y) / leg_length
                    depths.append(depth_ratio)
        
        if not depths:
            return 50.0, self.create_metric("depth", 50.0), []
        
        avg_depth = np.mean(depths)
        depth_score = self.calculate_score(avg_depth, ideal_depth - 0.1, ideal_depth + 0.1)
        metric = self.create_metric("depth", depth_score, value=round(avg_depth, 3), unit="ratio")
        
        feedback = []
        if depth_score >= 85:
            feedback.append(self.create_feedback("info", "Excellent depth achieved.", "depth"))
        elif depth_score < 60:
            feedback.append(self.create_feedback("critical", "Insufficient depth detected. Lower your hips until your thighs are parallel to the ground, or your hip crease is below your knee crease. Keep your chest up and core tight as you descend. Practice with bodyweight squats to build depth before adding weight.", "depth"))
        
        return depth_score, metric, feedback
    
    def analyze_bar_path(self, landmarks_list: List[Dict]) -> tuple[float, MetricScore, List[FeedbackItem]]:
        if not landmarks_list:
            return 50.0, self.create_metric("bar_path", 50.0), []
        
        path_deviations = []
        for landmarks in landmarks_list:
            if "left_shoulder" in landmarks and "right_shoulder" in landmarks:
                shoulder_center_x = (landmarks["left_shoulder"][0] + landmarks["right_shoulder"][0]) / 2
                ideal_path = 0.5
                deviation = abs(shoulder_center_x - ideal_path)
                path_deviations.append(deviation)
        
        if not path_deviations:
            return 50.0, self.create_metric("bar_path", 50.0), []
        
        avg_deviation = np.mean(path_deviations)
        path_score = max(0, 100 - (avg_deviation * 500))
        metric = self.create_metric("bar_path", path_score, value=round(avg_deviation, 3), unit="deviation")
        
        feedback = []
        if path_score >= 85:
            feedback.append(self.create_feedback("info", "Straight bar path maintained.", "bar_path"))
        elif path_score < 60:
            feedback.append(self.create_feedback("warning", "Bar path is deviating from ideal. Keep the bar directly over the middle of your foot throughout the entire lift. Think about dragging the bar close to your body - it should stay in contact with your legs during the movement. Practice with lighter weight focusing on maintaining a vertical bar path.", "bar_path"))
        
        return path_score, metric, feedback
    
    def analyze_spine_alignment(self, landmarks_list: List[Dict]) -> tuple[float, MetricScore, List[FeedbackItem]]:
        if not landmarks_list:
            return 50.0, self.create_metric("spine_alignment", 50.0), []
        
        alignment_scores = []
        for landmarks in landmarks_list:
            if all(k in landmarks for k in ["left_shoulder", "right_shoulder", "left_hip", "right_hip"]):
                shoulder_center_x = (landmarks["left_shoulder"][0] + landmarks["right_shoulder"][0]) / 2
                hip_center_x = (landmarks["left_hip"][0] + landmarks["right_hip"][0]) / 2
                
                deviation = abs(shoulder_center_x - hip_center_x)
                alignment = max(0, 100 - (deviation * 400))
                alignment_scores.append(alignment)
        
        if not alignment_scores:
            return 50.0, self.create_metric("spine_alignment", 50.0), []
        
        score = np.mean(alignment_scores)
        metric = self.create_metric("spine_alignment", score, value=round(score, 1))
        
        feedback = []
        if score >= 85:
            feedback.append(self.create_feedback("info", "Neutral spine maintained throughout.", "spine_alignment"))
        elif score < 60:
            feedback.append(self.create_feedback("critical", "CRITICAL: Spine rounding detected. Keep your chest up and shoulders back throughout the entire lift. Engage your core and maintain a slight arch in your lower back. If you cannot maintain a neutral spine, reduce the weight and focus on form. Consider doing core strengthening exercises to improve spinal stability.", "spine_alignment"))
        
        return score, metric, feedback
    
    def analyze_tempo(self, pose_data: List[Dict]) -> tuple[float, MetricScore, List[FeedbackItem]]:
        if len(pose_data) < 5:
            return 50.0, self.create_metric("tempo", 50.0), []
        
        frame_count = len(pose_data)
        ideal_tempo = 60
        
        tempo_score = self.calculate_score(frame_count, ideal_tempo * 0.7, ideal_tempo * 1.3)
        metric = self.create_metric("tempo", tempo_score, value=frame_count, unit="frames")
        
        feedback = []
        if tempo_score >= 85:
            feedback.append(self.create_feedback("info", "Good lifting tempo.", "tempo"))
        elif tempo_score < 60:
            feedback.append(self.create_feedback("warning", "Your lifting tempo needs adjustment. Control the descent for 2-3 seconds, pause briefly at the bottom, then explode up with control. Avoid bouncing or rushing the movement. Practice with a 2-1-2 tempo: 2 seconds down, 1 second pause, 2 seconds up.", "tempo"))
        
        return tempo_score, metric, feedback
    
    def analyze_joint_angles(self, angles_list: List[Dict], joint_name: str, ideal_angle: float, tolerance: float = 10.0) -> tuple[float, MetricScore, List[FeedbackItem]]:
        if not angles_list:
            return 50.0, self.create_metric(joint_name, 50.0), []
        
        angles = [angles.get(joint_name, ideal_angle) for angles in angles_list if joint_name in angles]
        
        if not angles:
            return 50.0, self.create_metric(joint_name, 50.0), []
        
        avg_angle = np.mean(angles)
        angle_score = self.calculate_score(avg_angle, ideal_angle - tolerance, ideal_angle + tolerance)
        metric = self.create_metric(joint_name, angle_score, value=round(avg_angle, 1), unit="degrees")
        
        feedback = []
        if angle_score >= 85:
            feedback.append(self.create_feedback("info", f"Good {joint_name} angle.", joint_name))
        elif angle_score < 60:
            # Provide specific, actionable feedback based on joint type
            if "knee" in joint_name.lower():
                if avg_angle > ideal_angle:
                    feedback.append(self.create_feedback("warning", f"Your {joint_name} is too straight (hyperextended). Maintain a slight bend in your knees throughout the movement. Think about keeping soft knees rather than locking them out. This will help protect your joints and improve movement efficiency.", joint_name))
                else:
                    feedback.append(self.create_feedback("warning", f"Your {joint_name} bend is insufficient. Increase knee flexion to achieve proper depth and muscle activation. Focus on pushing your knees out and sitting back into the movement.", joint_name))
            elif "hip" in joint_name.lower():
                if avg_angle > ideal_angle:
                    feedback.append(self.create_feedback("warning", f"Your {joint_name} is too extended. Hinge at the hips more by pushing your hips back and keeping your back straight. Think about closing the angle between your torso and thighs to activate your posterior chain.", joint_name))
                else:
                    feedback.append(self.create_feedback("warning", f"Your {joint_name} flexion is excessive. Maintain a more neutral hip position by keeping your pelvis in proper alignment. Engage your core to stabilize your hips.", joint_name))
            elif "elbow" in joint_name.lower():
                if avg_angle > ideal_angle:
                    feedback.append(self.create_feedback("warning", f"Your {joint_name} is too straight. Keep a slight bend in your elbows to maintain tension and protect the joint. Avoid locking out completely at the top of the movement.", joint_name))
                else:
                    feedback.append(self.create_feedback("warning", f"Your {joint_name} is too bent. Extend your arms more fully through the movement while maintaining control. Think about driving your elbows back and fully extending at the top.", joint_name))
            else:
                feedback.append(self.create_feedback("warning", f"{joint_name} angle is outside the ideal range of {ideal_angle - tolerance:.0f}-{ideal_angle + tolerance:.0f} degrees. Your current angle is {avg_angle:.1f} degrees. Focus on adjusting your positioning to bring this joint into the optimal range for this lift.", joint_name))
        
        return angle_score, metric, feedback






