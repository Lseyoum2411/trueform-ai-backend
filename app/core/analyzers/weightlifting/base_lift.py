from abc import ABC
from typing import List, Dict
import numpy as np
from app.core.analyzers.base import BaseAnalyzer
from app.models.analysis import MetricScore, FeedbackItem


class BaseLiftAnalyzer(BaseAnalyzer, ABC):
    def analyze_depth(self, landmarks_list: List[Dict], ideal_depth: float, lift_type: str = "general") -> tuple[float, MetricScore, List[FeedbackItem]]:
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
            if lift_type in ["barbell_row", "dumbbell_row"]:
                feedback.append(self.create_beginner_feedback(
                    "critical",
                    "depth",
                    "You are not bending forward enough when you pull the weight.",
                    [
                        "Bend forward like you are closing a car door with your hips",
                        "Stop when your chest points toward the floor",
                        "Your back should be at about a 45-degree angle to the floor",
                        "Hold this position while you pull"
                    ],
                    "Your hips should feel like a hinge opening and closing, not like you are squatting down.",
                    "Do not stand straight up or squat down. You should be bent forward.",
                    "Film from the side. Your upper body should be angled forward, not straight up."
                ))
            else:
                feedback.append(self.create_beginner_feedback(
                    "critical",
                    "depth",
                    "You are not going low enough in this exercise.",
                    [
                        "Lower your body until your thighs are parallel to the floor, like sitting in a chair",
                        "Go down until your hips are at the same level as your knees",
                        "Keep your chest up and look straight ahead",
                        "Push through your heels to stand back up"
                    ],
                    "Your legs should feel like they are working hard, like you are sitting down and standing up from a low chair.",
                    "Do not stop halfway down. Go all the way down until your thighs are parallel to the floor.",
                    "Film from the side. At the bottom, your thigh should be parallel to the floor."
                ))
        
        return depth_score, metric, feedback
    
    def analyze_bar_path(self, landmarks_list: List[Dict], lift_type: str = "general") -> tuple[float, MetricScore, List[FeedbackItem]]:
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
            if lift_type in ["barbell_row", "dumbbell_row"]:
                feedback.append(self.create_beginner_feedback(
                    "warning",
                    "bar_path",
                    "The bar is not moving in a straight line when you pull.",
                    [
                        "Pull the bar straight toward your belly button, not your chest",
                        "Keep the bar close to your body the whole time",
                        "Imagine drawing a straight line from where the bar starts to your belly button",
                        "Do not pull the bar up toward your shoulders"
                    ],
                    "The bar should feel like it is scraping against your shirt as it moves toward your stomach.",
                    "Do not pull the bar up toward your chest or shoulders. Pull it toward your belly.",
                    "Film from the side. The bar should move in a straight line toward your body, not up and down."
                ))
            else:
                feedback.append(self.create_beginner_feedback(
                    "warning",
                    "bar_path",
                    "The bar is not moving in a straight line.",
                    [
                        "Keep the bar directly over the middle of your foot",
                        "Think about moving the bar straight up and straight down",
                        "Do not let the bar drift forward or backward",
                        "Practice with no weight or light weight to feel the straight path"
                    ],
                    "The bar should feel like it is going straight up and down, like an elevator.",
                    "Do not swing the bar forward or backward. Keep it in a straight line.",
                    "Film from the side. Draw an imaginary line up from your foot - the bar should follow it."
                ))
        
        return path_score, metric, feedback
    
    def analyze_spine_alignment(self, landmarks_list: List[Dict], lift_type: str = "general") -> tuple[float, MetricScore, List[FeedbackItem]]:
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
            if lift_type in ["barbell_row", "dumbbell_row"]:
                feedback.append(self.create_beginner_feedback(
                    "critical",
                    "spine_alignment",
                    "Your back rounds when you pull the bar.",
                    [
                        "Bend forward like you are closing a car door with your hips",
                        "Stop when your chest points toward the floor",
                        "Keep your chest in the same position the entire time",
                        "Pull the bar toward your belly, not your chest"
                    ],
                    "Your back should feel tight and strong, like it is locked in place.",
                    "Do not stand up as you pull the weight.",
                    "Film from the side. Your chest should not move up and down."
                ))
            else:
                feedback.append(self.create_beginner_feedback(
                    "critical",
                    "spine_alignment",
                    "Your back is rounding or arching too much.",
                    [
                        "Keep your chest up like you are proud",
                        "Look straight ahead, not down at the floor",
                        "Keep your back straight like a table, not curved like a banana",
                        "If your back starts to round, use less weight"
                    ],
                    "Your back should feel strong and straight, like you are standing up tall with good posture.",
                    "Do not let your back curve or round. Keep it straight like a board.",
                    "Film from the side. Your back should be straight, not curved in either direction."
                ))
        
        return score, metric, feedback
    
    def analyze_tempo(self, pose_data: List[Dict], lift_type: str = "general") -> tuple[float, MetricScore, List[FeedbackItem]]:
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
            if lift_type in ["barbell_row", "dumbbell_row"]:
                feedback.append(self.create_beginner_feedback(
                    "warning",
                    "tempo",
                    "The weight moves by swinging, not pulling.",
                    [
                        "Start with the bar completely still",
                        "Pull the bar smoothly, not fast",
                        "Lower it slower than you lift it",
                        "Control the weight the whole time"
                    ],
                    "The movement should feel controlled, not explosive.",
                    "Do not use your legs to start the pull.",
                    "If the plates make noise, you are swinging."
                ))
            else:
                feedback.append(self.create_beginner_feedback(
                    "warning",
                    "tempo",
                    "You are moving too fast or too slow.",
                    [
                        "Go down slowly, counting to 2",
                        "Pause for 1 second at the bottom",
                        "Come back up slowly, counting to 2",
                        "Do not rush or bounce"
                    ],
                    "The movement should feel smooth and controlled, like slow motion.",
                    "Do not drop down fast or bounce at the bottom. Move slowly and smoothly.",
                    "Count in your head: 2 seconds down, pause, 2 seconds up."
                ))
        
        return tempo_score, metric, feedback
    
    def analyze_joint_angles(self, angles_list: List[Dict], joint_name: str, ideal_angle: float, tolerance: float = 10.0, lift_type: str = "general") -> tuple[float, MetricScore, List[FeedbackItem]]:
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
            # Provide beginner-friendly feedback based on joint type and exercise
            if "elbow" in joint_name.lower():
                if lift_type == "dumbbell_row":
                    if avg_angle < ideal_angle:
                        feedback.append(self.create_beginner_feedback(
                            "warning",
                            joint_name,
                            "You are lifting the dumbbell mostly with your arm.",
                            [
                                "Place one hand and one knee on a bench",
                                "Let the dumbbell hang straight down",
                                "Pull your elbow back toward your back pocket",
                                "Lower the weight slowly until your arm is straight again"
                            ],
                            "You should feel the pull in your upper back, not your bicep.",
                            "Do not pull the dumbbell straight up toward your shoulder.",
                            "At the top, your elbow should be close to your body, not flared out."
                        ))
                    else:
                        feedback.append(self.create_beginner_feedback(
                            "warning",
                            joint_name,
                            "Your elbow is too straight when you pull the dumbbell.",
                            [
                                "Place one hand and one knee on a bench",
                                "Bend your elbow more as you pull the dumbbell",
                                "Keep your elbow at about 90 degrees when the weight is close to your body",
                                "Think about bringing the weight to your body, not away from it"
                            ],
                            "Your elbow should feel bent, like you are rowing a boat.",
                            "Do not keep your arm completely straight. Bend your elbow as you pull.",
                            "When the weight is close to your body, your elbow should be bent, not straight."
                        ))
                elif lift_type == "barbell_row":
                    if avg_angle < ideal_angle:
                        feedback.append(self.create_beginner_feedback(
                            "warning",
                            joint_name,
                            "Your elbow is too bent when you pull.",
                            [
                                "Pull your elbow back toward your back pocket",
                                "Keep your elbow close to your body",
                                "Think about squeezing your shoulder blades together",
                                "Do not pull straight up with just your arm"
                            ],
                            "You should feel the pull in your upper back, not your bicep.",
                            "Do not pull the weight straight up toward your shoulder.",
                            "At the top, your elbow should be close to your body, not flared out."
                        ))
                    else:
                        feedback.append(self.create_beginner_feedback(
                            "warning",
                            joint_name,
                            "Your elbow is too straight when you pull.",
                            [
                                "Bend your elbow more as you pull",
                                "Keep your elbow at about 90 degrees when the weight is close to your body",
                                "Do not lock your elbow straight",
                                "Think about bringing the weight to your body, not away from it"
                            ],
                            "Your elbow should feel bent, like you are rowing a boat.",
                            "Do not keep your arm completely straight. Bend your elbow as you pull.",
                            "When the weight is close to your body, your elbow should be bent, not straight."
                        ))
                else:
                    if avg_angle > ideal_angle:
                        feedback.append(self.create_beginner_feedback(
                            "warning",
                            joint_name,
                            "Your elbow is too straight.",
                            [
                                "Keep a slight bend in your elbow, do not lock it",
                                "Think about keeping soft elbows, not stiff ones",
                                "Bend your elbow just a little bit all the time"
                            ],
                            "Your elbow should feel relaxed, not locked straight.",
                            "Do not lock your elbow completely straight. Keep it slightly bent.",
                            "Look at your elbow in a mirror. It should have a small bend, not be completely straight."
                        ))
                    else:
                        feedback.append(self.create_beginner_feedback(
                            "warning",
                            joint_name,
                            "Your elbow is too bent.",
                            [
                                "Straighten your arm more during the movement",
                                "Push or pull through your full range of motion",
                                "Do not stop halfway - go all the way"
                            ],
                            "Your arm should feel like it is moving through its full range.",
                            "Do not keep your elbow too bent. Straighten it more.",
                            "At the end of the movement, your arm should be straighter, not still bent."
                        ))
            elif "hip" in joint_name.lower():
                if lift_type in ["barbell_row", "dumbbell_row"]:
                    feedback.append(self.create_beginner_feedback(
                        "warning",
                        joint_name,
                        "Your hip position is not right for pulling the weight.",
                        [
                            "Bend forward from your hips, like closing a car door",
                            "Keep your hips in the same place while you pull",
                            "Do not move your hips up and down",
                            "Your hips should stay still, only your arms should move"
                        ],
                        "Your hips should feel like they are locked in place, like a hinge that is not moving.",
                        "Do not stand up or squat down. Keep your hips in one position.",
                        "Film from the side. Your hips should stay at the same height the whole time."
                    ))
                else:
                    if avg_angle > ideal_angle:
                        feedback.append(self.create_beginner_feedback(
                            "warning",
                            joint_name,
                            "Your hips are too straight.",
                            [
                                "Push your hips back, like you are closing a door with your butt",
                                "Bend forward from your hips, not your back",
                                "Keep your back straight while you push your hips back"
                            ],
                            "Your hips should feel like they are moving backward, like a door hinge.",
                            "Do not bend from your back. Bend from your hips.",
                            "Stand sideways to a mirror. Your hips should move back, not down like squatting."
                        ))
                    else:
                        feedback.append(self.create_beginner_feedback(
                            "warning",
                            joint_name,
                            "Your hips are too bent forward.",
                            [
                                "Stand up straighter",
                                "Keep your hips more in line with your body",
                                "Do not lean forward too much"
                            ],
                            "Your hips should feel more upright, not bent forward.",
                            "Do not lean forward too far. Stand up straighter.",
                            "Stand sideways to a mirror. Your body should be more upright, not bent forward."
                        ))
            elif "knee" in joint_name.lower():
                if avg_angle > ideal_angle:
                    feedback.append(self.create_beginner_feedback(
                        "warning",
                        joint_name,
                        "Your knee is too straight.",
                        [
                            "Bend your knee a little bit, do not lock it",
                            "Keep soft knees, not stiff straight ones",
                            "Think about keeping your knee slightly bent all the time"
                        ],
                        "Your knee should feel relaxed, not locked straight.",
                        "Do not lock your knee completely straight. Keep it slightly bent.",
                        "Look at your knee. It should have a small bend, not be completely straight."
                    ))
                else:
                    feedback.append(self.create_beginner_feedback(
                        "warning",
                        joint_name,
                        "Your knee is not bent enough.",
                        [
                            "Bend your knee more, like you are sitting in a chair",
                            "Lower your body more",
                            "Push your knees out as you go down"
                        ],
                        "Your knee should feel like it is working hard, like going up and down stairs.",
                        "Do not keep your knee too straight. Bend it more.",
                        "At the bottom, your knee should be bent, not straight."
                    ))
            else:
                feedback.append(self.create_feedback("warning", f"{joint_name} angle needs adjustment. Focus on proper positioning for this movement.", joint_name))
        
        return angle_score, metric, feedback






