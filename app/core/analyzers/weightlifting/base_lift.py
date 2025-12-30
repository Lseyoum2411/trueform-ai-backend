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
                        "Go down slowly with control",
                        "Pause briefly at the bottom",
                        "Come back up slowly with control",
                        "Do not rush or bounce"
                    ],
                    "The movement should feel smooth and controlled, like slow motion.",
                    "Do not drop down fast or bounce at the bottom. Move slowly and smoothly.",
                    "Move slowly and deliberately: down with control, pause briefly, then up with control."
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
    
    def analyze_knee_alignment_squat(self, landmarks_list: List[Dict], angles_list: List[Dict]) -> tuple[float, MetricScore, List[FeedbackItem]]:
        """Squat specific: Analyze knee alignment - knees should track over toes, not cave inward."""
        if not landmarks_list or not angles_list:
            return 50.0, self.create_metric("knee_alignment", 50.0), []
        
        knee_valgus_scores = []
        for landmarks in landmarks_list:
            if all(k in landmarks for k in ["left_knee", "left_ankle", "right_knee", "right_ankle"]):
                # Calculate knee position relative to ankle (valgus collapse)
                left_knee_x = landmarks["left_knee"][0]
                left_ankle_x = landmarks["left_ankle"][0]
                right_knee_x = landmarks["right_knee"][0]
                right_ankle_x = landmarks["right_ankle"][0]
                
                # For proper alignment, knee should be over or slightly outside ankle
                # Valgus (caving in) = knee X < ankle X (for right side) or knee X > ankle X (for left side)
                left_valgus = left_ankle_x - left_knee_x  # Positive = knee inside ankle (valgus)
                right_valgus = right_knee_x - right_ankle_x  # Positive = knee inside ankle (valgus)
                
                # Use the worse side
                max_valgus = max(abs(left_valgus), abs(right_valgus))
                # Score: 0 deviation = perfect, higher deviation = worse
                alignment_score = max(0, 100 - (max_valgus * 1000))
                knee_valgus_scores.append(alignment_score)
        
        if not knee_valgus_scores:
            return 50.0, self.create_metric("knee_alignment", 50.0), []
        
        score = np.mean(knee_valgus_scores)
        metric = self.create_metric("knee_alignment", score, value=round(score, 1))
        
        feedback = []
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent knee alignment — knees tracking over toes.", "knee_alignment"))
        elif score < 60:
            feedback.append(self.create_beginner_feedback(
                "critical",
                "knee_alignment",
                "Your knees tend to cave inward on the way up. This form issue reduces the effectiveness of the squat and could risk injury.",
                [
                    "Push your knees outward in line with your toes as you both descend and ascend",
                    "Actively think about spreading the floor with your feet — this engages your glutes and stops the knees from buckling inward",
                    "Keep your knees pushed out the entire time, not just at the bottom",
                    "Think about rotating your feet outward slightly to help your knees track correctly"
                ],
                "Your knees should feel like they are pushing outward, like you are trying to spread the floor apart with your feet.",
                "Do not let your knees cave inward. Push them outward over your toes.",
                "Box squat practice: Use a box or bench set at just about parallel height. Squat down until you just touch your butt to the box (don't sit fully, just a light tap) and come back up. The box gives you a depth target and confidence to sit back into your squat. Complete several sets with multiple reps using a light weight, focusing on knees out and consistent depth each rep."
            ))
        else:
            feedback.append(self.create_beginner_feedback(
                "warning",
                "knee_alignment",
                "Your knee alignment can be improved for safer and more effective squats.",
                [
                    "Push your knees outward in line with your toes as you descend and ascend",
                    "Think about spreading the floor with your feet to engage your glutes",
                    "Keep your knees tracking over your toes throughout the movement"
                ],
                "Your knees should feel like they are pushing outward, engaging your glutes.",
                "Do not let your knees cave inward. Keep them over your toes.",
                "Film from the front to check that your knees stay over your toes."
            ))
        
        return score, metric, feedback
    
    def analyze_depth_squat(self, landmarks_list: List[Dict], ideal_depth: float) -> tuple[float, MetricScore, List[FeedbackItem]]:
        """Squat specific: Analyze depth with enhanced feedback for parallel depth requirement."""
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
            feedback.append(self.create_feedback("info", "Excellent depth — thighs reaching parallel or below.", "depth"))
        elif depth_score < 60:
            feedback.append(self.create_beginner_feedback(
                "critical",
                "depth",
                "You're not squatting to full depth (thighs aren't reaching parallel to the floor) and your knees tend to cave inward on the way up. These form issues reduce the effectiveness of the squat and could risk injury.",
                [
                    "Go deep (within safe limits). Aim to lower until your thighs are at least parallel to the ground. If you can go slightly below parallel with good form, that's great",
                    "Keep your heels down and weight balanced mid-foot as you hit depth",
                    "Keep your chest up and core tight. Look forward or slightly up to help keep your torso upright",
                    "A strong core will help you maintain posture so you can reach depth without collapsing forward"
                ],
                "Your legs should feel like they are working hard, like you are sitting down and standing up from a low chair.",
                "Do not stop halfway down. Go all the way down until your thighs are parallel to the floor.",
                "Box squat practice: Use a box or bench set at just about parallel height. Squat down until you just touch your butt to the box (don't sit fully, just a light tap) and come back up. Do 3 sets of 8 reps with a light weight, focusing on knees out and consistent depth each rep."
            ))
        else:
            feedback.append(self.create_beginner_feedback(
                "warning",
                "depth",
                "Your squat depth can be improved to fully engage your glutes and hamstrings.",
                [
                    "Lower until your thighs are at least parallel to the ground",
                    "Keep your heels down and weight balanced mid-foot",
                    "Keep your chest up and core tight to maintain posture"
                ],
                "Your legs should feel like they are working hard, engaging both your quads and glutes.",
                "Do not stop short of parallel. Go all the way down.",
                "Film from the side to check that your thighs reach parallel to the floor."
            ))
        
        return depth_score, metric, feedback
    
    def analyze_elbow_position_front_squat(self, landmarks_list: List[Dict], angles_list: List[Dict]) -> tuple[float, MetricScore, List[FeedbackItem]]:
        """Front squat specific: Analyze elbow position - elbows should stay high."""
        if not landmarks_list or not angles_list:
            return 50.0, self.create_metric("elbow_position", 50.0), []
        
        elbow_heights = []
        for landmarks in landmarks_list:
            if "left_elbow" in landmarks and "left_shoulder" in landmarks:
                elbow_y = landmarks["left_elbow"][1]
                shoulder_y = landmarks["left_shoulder"][1]
                # Higher elbows = lower Y value (closer to shoulder level)
                # Elbows should be at or above shoulder level
                elbow_height = shoulder_y - elbow_y  # Positive = elbow above shoulder (good)
                elbow_heights.append(elbow_height)
        
        if not elbow_heights:
            return 50.0, self.create_metric("elbow_position", 50.0), []
        
        avg_elbow_height = np.mean(elbow_heights)
        # Ideal: elbows at shoulder level or slightly above (0 to 0.05)
        ideal_height = 0.02
        if avg_elbow_height >= ideal_height:
            score = 100.0
        elif avg_elbow_height >= -0.02:
            score = 70.0 + ((avg_elbow_height + 0.02) / (ideal_height + 0.02)) * 30.0
        else:
            score = max(0, (avg_elbow_height + 0.05) / 0.03 * 70.0)
        
        score = min(100, max(0, score))
        metric = self.create_metric("elbow_position", score, value=round(avg_elbow_height, 3))
        
        feedback = []
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent elbow position — elbows high throughout.", "elbow_position"))
        elif score < 60:
            feedback.append(self.create_beginner_feedback(
                "critical",
                "elbow_position",
                "During front squats, your elbows drop and your torso leans forward, causing the bar to tilt forward off your shoulders. This makes the lift harder and strains your wrists/arms as you try to hold the bar.",
                [
                    "Drive your elbows toward the ceiling throughout the squat. As soon as you unrack the bar, get your elbows up high (upper arms at least parallel to the ground) and maintain that as you squat down and up",
                    "Keep your chest lifted. Think \"proud chest\" or imagine showing the logo on your shirt to someone in front of you",
                    "Take a big breath and brace your core before descending to help stabilize your torso",
                    "If you feel them dropping, fight to raise them again"
                ],
                "Your elbows should feel like they are pointing straight up toward the ceiling, keeping the bar secure on your shoulders.",
                "Do not let your elbows drop. Keep them high the entire time.",
                "Look in a mirror from the side. Your elbows should stay at shoulder level or higher throughout the squat."
            ))
        else:
            feedback.append(self.create_beginner_feedback(
                "warning",
                "elbow_position",
                "Your elbow position can be improved to keep the bar secure on your shoulders.",
                [
                    "Drive your elbows toward the ceiling throughout the squat",
                    "Keep your chest lifted — think \"proud chest\"",
                    "Brace your core before descending"
                ],
                "Your elbows should feel like they are pointing up, keeping the bar secure.",
                "Do not let your elbows drop. Keep them high.",
                "Check in a mirror that your elbows stay at shoulder level or higher."
            ))
        
        return score, metric, feedback
    
    def analyze_spine_alignment_deadlift(self, landmarks_list: List[Dict]) -> tuple[float, MetricScore, List[FeedbackItem]]:
        """Deadlift specific: Analyze flat back and core tightness."""
        if not landmarks_list:
            return 50.0, self.create_metric("spine_alignment", 50.0), []
        
        alignment_scores = []
        for landmarks in landmarks_list:
            if all(k in landmarks for k in ["left_shoulder", "right_shoulder", "left_hip", "right_hip"]):
                shoulder_center_x = (landmarks["left_shoulder"][0] + landmarks["right_shoulder"][0]) / 2
                hip_center_x = (landmarks["left_hip"][0] + landmarks["right_hip"][0]) / 2
                
                # For deadlift, we want minimal deviation (flat back)
                deviation = abs(shoulder_center_x - hip_center_x)
                alignment = max(0, 100 - (deviation * 500))  # Stricter threshold for deadlift
                alignment_scores.append(alignment)
        
        if not alignment_scores:
            return 50.0, self.create_metric("spine_alignment", 50.0), []
        
        score = np.mean(alignment_scores)
        metric = self.create_metric("spine_alignment", score, value=round(score, 1))
        
        feedback = []
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent flat back maintained throughout deadlift.", "spine_alignment"))
        elif score < 60:
            feedback.append(self.create_beginner_feedback(
                "critical",
                "spine_alignment",
                "Your lower back rounds during the deadlift, especially as you begin to pull the bar off the floor. This indicates a loss of a neutral spine during the lift.",
                [
                    "Set your back before you lift. Grip the bar, then tighten your core (imagine someone is about to punch your stomach) and pull your shoulder blades slightly down and back",
                    "Hips down, chest up. Lower your hips a bit and lift your chest as you start the pull. Your shins should touch the bar and your gaze should be forward or slightly up",
                    "If you feel your back starting to round at any point, stop and reset. It's better to do a perfect rep with lighter weight than a bad rep with heavy weight"
                ],
                "Your back should feel tight and strong, like it is locked in place and cannot bend.",
                "Do not let your back round. Keep it flat like a table.",
                "Film from the side. Your back should be straight from your shoulders to your hips, not curved."
            ))
        else:
            feedback.append(self.create_beginner_feedback(
                "warning",
                "spine_alignment",
                "Your back position can be improved for safer and more efficient deadlifts.",
                [
                    "Set your back before you lift — tighten your core and pull shoulder blades down and back",
                    "Hips down, chest up as you start the pull",
                    "If your back rounds, reduce the weight and reset"
                ],
                "Your back should feel tight and flat, like it is locked in place.",
                "Do not let your back round. Keep it flat.",
                "Film from the side to check that your back stays straight."
            ))
        
        return score, metric, feedback
    
    def analyze_hip_hinge_rdl(self, landmarks_list: List[Dict], angles_list: List[Dict]) -> tuple[float, MetricScore, List[FeedbackItem]]:
        """RDL specific: Analyze proper hip hinge - minimal knee bend, flat back."""
        if not landmarks_list or not angles_list:
            return 50.0, self.create_metric("hip_hinge", 50.0), []
        
        knee_angles = []
        for angles in angles_list:
            if "left_knee" in angles:
                knee_angles.append(angles["left_knee"])
        
        if not knee_angles:
            return 50.0, self.create_metric("hip_hinge", 50.0), []
        
        avg_knee_angle = np.mean(knee_angles)
        # RDL should have minimal knee bend (~170 degrees = almost straight)
        ideal_knee = 170.0
        knee_deviation = abs(avg_knee_angle - ideal_knee)
        
        # Score based on how close knee is to straight (170 degrees)
        if knee_deviation <= 10:
            score = 100.0
        elif knee_deviation <= 20:
            score = 85.0
        elif knee_deviation <= 30:
            score = 70.0
        else:
            score = max(0, 100 - (knee_deviation - 30) * 2)
        
        score = min(100, max(0, score))
        metric = self.create_metric("hip_hinge", score, value=round(avg_knee_angle, 1), unit="degrees")
        
        feedback = []
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent hip hinge — minimal knee bend, proper RDL form.", "hip_hinge"))
        elif score < 60:
            feedback.append(self.create_beginner_feedback(
                "critical",
                "hip_hinge",
                "In the Romanian deadlift (RDL), you are bending your knees too much or letting your back round, effectively turning it into a partial squat instead of a pure hip hinge.",
                [
                    "Start with a soft bend in your knees (maybe 15 degrees) and keep that same bend throughout the movement",
                    "Don't squat down; instead, push your butt backward as if you're trying to touch an imaginary wall behind you",
                    "Maintain a flat back from start to finish. Stick your chest out a bit and keep your shoulders pulled back",
                    "Lower the bar until you feel a stretch in your hamstrings, typically when it's just below your knees or mid-shin (depending on flexibility). You don't need to touch the floor"
                ],
                "Your hips should feel like they are moving backward like a door hinge, not down like a squat.",
                "Do not squat down. Push your hips back while keeping your knees almost straight.",
                "Film from the side. Your hips should move backward, not down, and your knees should stay almost straight."
            ))
        else:
            feedback.append(self.create_beginner_feedback(
                "warning",
                "hip_hinge",
                "Your hip hinge can be improved for better RDL form.",
                [
                    "Keep a soft bend in your knees (about 15 degrees) and maintain it",
                    "Push your butt backward, don't squat down",
                    "Maintain a flat back throughout"
                ],
                "Your hips should feel like they are moving backward like a hinge.",
                "Do not bend your knees too much. Keep them almost straight.",
                "Film from the side to check that your hips move back, not down."
            ))
        
        return score, metric, feedback
    
    def analyze_back_tightness_bench(self, landmarks_list: List[Dict]) -> tuple[float, MetricScore, List[FeedbackItem]]:
        """Bench press specific: Analyze shoulder blade retraction (tight back)."""
        if not landmarks_list:
            return 50.0, self.create_metric("back_tightness", 50.0), []
        
        shoulder_distances = []
        for landmarks in landmarks_list:
            if "left_shoulder" in landmarks and "right_shoulder" in landmarks:
                # Retracted shoulder blades = shoulders closer together
                shoulder_distance = abs(landmarks["left_shoulder"][0] - landmarks["right_shoulder"][0])
                shoulder_distances.append(shoulder_distance)
        
        if not shoulder_distances:
            return 50.0, self.create_metric("back_tightness", 50.0), []
        
        # For bench, we want shoulders closer (retracted) - lower distance = better
        avg_distance = np.mean(shoulder_distances)
        # Use a reference - need to compare to typical shoulder width
        # Assume ideal retracted distance is ~0.8x normal shoulder width
        ideal_distance = 0.15  # Approximate
        deviation = abs(avg_distance - ideal_distance)
        
        if deviation <= 0.02:
            score = 100.0
        else:
            score = max(0, 100 - (deviation / 0.02) * 30)
        
        score = min(100, max(0, score))
        metric = self.create_metric("back_tightness", score, value=round(avg_distance, 3))
        
        feedback = []
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent back tightness — shoulder blades retracted.", "back_tightness"))
        elif score < 60:
            feedback.append(self.create_beginner_feedback(
                "critical",
                "back_tightness",
                "When you bench press, your shoulder blades are not retracted (your back is loose on the bench) and your elbows flare out to the sides. This makes the lift feel harder and can strain your shoulders.",
                [
                    "Before you unrack the bar, lie down and squeeze your shoulder blades together and down (imagine pinching a pencil between them)",
                    "Maintain this scapular retraction throughout the lift; your upper back should stay tight against the bench",
                    "Position your elbows at about a 45-degree angle from your body as you lower the bar",
                    "Keep your whole body tight. Plant your feet firmly on the floor and drive through your legs slightly"
                ],
                "Your upper back should feel tight and pressed into the bench, like you are pinching your shoulder blades together.",
                "Do not let your back come loose. Keep your shoulder blades squeezed together the entire time.",
                "Have someone check or film from above. Your shoulder blades should be pulled back and down, not loose."
            ))
        else:
            feedback.append(self.create_beginner_feedback(
                "warning",
                "back_tightness",
                "Your back tightness can be improved for more powerful and safe bench presses.",
                [
                    "Squeeze your shoulder blades together and down before unracking",
                    "Maintain this tightness throughout the lift",
                    "Keep your elbows at about 45 degrees, not flared out"
                ],
                "Your upper back should feel tight and pressed into the bench.",
                "Do not let your back come loose. Keep your shoulder blades squeezed together.",
                "Check that your shoulder blades stay retracted throughout the lift."
            ))
        
        return score, metric, feedback
    
    def analyze_torso_stability_row(self, landmarks_list: List[Dict]) -> tuple[float, MetricScore, List[FeedbackItem]]:
        """Row specific: Analyze torso stability - no jerking or standing up."""
        if not landmarks_list or len(landmarks_list) < 5:
            return 50.0, self.create_metric("torso_stability", 50.0), []
        
        torso_angles = []
        for landmarks in landmarks_list:
            if all(k in landmarks for k in ["left_shoulder", "right_shoulder", "left_hip", "right_hip"]):
                shoulder_center_x = (landmarks["left_shoulder"][0] + landmarks["right_shoulder"][0]) / 2
                hip_center_x = (landmarks["left_hip"][0] + landmarks["right_hip"][0]) / 2
                shoulder_center_y = (landmarks["left_shoulder"][1] + landmarks["right_shoulder"][1]) / 2
                hip_center_y = (landmarks["left_hip"][1] + landmarks["right_hip"][1]) / 2
                
                # Calculate torso angle (should be consistent for strict rows)
                # For row, torso should be angled forward consistently
                if abs(hip_center_x - shoulder_center_x) > 0.001:
                    angle = np.arctan2(hip_center_y - shoulder_center_y, abs(hip_center_x - shoulder_center_x))
                    torso_angles.append(angle)
        
        if len(torso_angles) < 3:
            return 50.0, self.create_metric("torso_stability", 50.0), []
        
        # Check consistency - low variance = stable torso
        angle_variance = np.var(torso_angles)
        if angle_variance <= 0.001:
            score = 100.0
        elif angle_variance <= 0.005:
            score = 85.0
        elif angle_variance <= 0.01:
            score = 70.0
        else:
            score = max(0, 100 - (angle_variance - 0.01) * 5000)
        
        score = min(100, max(0, score))
        metric = self.create_metric("torso_stability", score, value=round(angle_variance, 4))
        
        feedback = []
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent torso stability — strict row form maintained.", "torso_stability"))
        elif score < 60:
            feedback.append(self.create_beginner_feedback(
                "critical",
                "torso_stability",
                "You tend to use momentum and raise your torso upright when doing barbell rows, and your back may round. This means you're not isolating your back muscles fully and could hurt your lower back.",
                [
                    "Set your back and stance before the row. Bend at the hips so your chest is facing the ground at about a 45-degree angle (or even closer to parallel for a strict row)",
                    "Keep your knees slightly bent and back flat (no hunching). Think about sticking your butt out and bracing your abs",
                    "Pull with your elbows. As you row the bar toward you, drive your elbows up and back, bringing the bar toward your lower chest or upper abdomen",
                    "Lower the bar under control until your arms are straight, all while keeping your torso in basically the same position (don't stand up between reps)"
                ],
                "Your torso should feel locked in place, like you are bent forward and staying there the entire time.",
                "Do not stand up as you pull. Keep your torso at the same angle the whole time.",
                "Film from the side. Your torso angle should not change — you should not stand up between reps."
            ))
        else:
            feedback.append(self.create_beginner_feedback(
                "warning",
                "torso_stability",
                "Your torso stability can be improved for better back muscle isolation.",
                [
                    "Set your torso angle before the row and keep it there",
                    "Keep your back flat and core braced",
                    "Pull with your elbows, don't stand up as you pull"
                ],
                "Your torso should feel locked in place, bent forward and staying there.",
                "Do not stand up as you pull. Keep your torso angle constant.",
                "Film from the side to check that your torso angle doesn't change."
            ))
        
        return score, metric, feedback
    
    def analyze_torso_stability_dumbbell_row(self, landmarks_list: List[Dict]) -> tuple[float, MetricScore, List[FeedbackItem]]:
        """Dumbbell row specific: Analyze torso stability - no twisting."""
        if not landmarks_list or len(landmarks_list) < 5:
            return 50.0, self.create_metric("torso_stability", 50.0), []
        
        shoulder_levels = []
        for landmarks in landmarks_list:
            if "left_shoulder" in landmarks and "right_shoulder" in landmarks:
                # For stable torso, shoulders should be level (similar Y position)
                shoulder_level_diff = abs(landmarks["left_shoulder"][1] - landmarks["right_shoulder"][1])
                shoulder_levels.append(shoulder_level_diff)
        
        if not shoulder_levels:
            return 50.0, self.create_metric("torso_stability", 50.0), []
        
        avg_level_diff = np.mean(shoulder_levels)
        # Low difference = level shoulders = stable torso
        if avg_level_diff <= 0.01:
            score = 100.0
        elif avg_level_diff <= 0.02:
            score = 85.0
        elif avg_level_diff <= 0.04:
            score = 70.0
        else:
            score = max(0, 100 - (avg_level_diff - 0.04) * 1500)
        
        score = min(100, max(0, score))
        metric = self.create_metric("torso_stability", score, value=round(avg_level_diff, 3))
        
        feedback = []
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent torso stability — no twisting during dumbbell row.", "torso_stability"))
        elif score < 60:
            feedback.append(self.create_beginner_feedback(
                "critical",
                "torso_stability",
                "When doing one-arm dumbbell rows, you sometimes twist your torso and yank with your arm, which takes tension off your back muscles and can strain your spine.",
                [
                    "Set up with one hand and one knee on a bench (or in a staggered stance with one hand braced on something) so your upper body is roughly parallel to the floor",
                    "Brace your core as if preparing for a punch — this will keep your torso from twisting",
                    "Let the dumbbell hang straight down from your shoulder to start. Lead the pull with your elbow: drive it up toward the ceiling, keeping it close to your body",
                    "Keep your shoulders level and square to the ground. As you row, do not let your working shoulder dip down or your opposite shoulder rise up. Likewise, avoid turning your chest to face the ceiling"
                ],
                "Your torso should feel like a plank — completely still and stable, with only your arm moving.",
                "Do not twist your torso. Keep it completely still and level.",
                "Film from behind or have someone watch. Your shoulders should stay level — no twisting or rotating."
            ))
        else:
            feedback.append(self.create_beginner_feedback(
                "warning",
                "torso_stability",
                "Your torso stability can be improved to better isolate your back muscles.",
                [
                    "Brace your core to keep your torso from twisting",
                    "Keep your shoulders level and square to the ground",
                    "Only your arm should move — your body should remain still like a plank"
                ],
                "Your torso should feel like a plank — completely still and stable.",
                "Do not twist your torso. Keep it still and level.",
                "Check that your shoulders stay level throughout the movement."
            ))
        
        return score, metric, feedback
    
    def analyze_range_of_motion_pulldown(self, landmarks_list: List[Dict]) -> tuple[float, MetricScore, List[FeedbackItem]]:
        """Lat pulldown specific: Analyze full range of motion - bar to chest."""
        if not landmarks_list:
            return 50.0, self.create_metric("range_of_motion", 50.0), []
        
        # Analyze wrist position relative to chest/shoulders at bottom of movement
        # Lower wrist = better (full range)
        bottom_frames = landmarks_list[len(landmarks_list) // 2:]
        wrist_positions = []
        
        for landmarks in bottom_frames:
            if "left_wrist" in landmarks and "left_shoulder" in landmarks:
                wrist_y = landmarks["left_wrist"][1]
                shoulder_y = landmarks["left_shoulder"][1]
                # Wrist should be near or below shoulder level at bottom
                wrist_relative = wrist_y - shoulder_y  # Positive = wrist below shoulder (good)
                wrist_positions.append(wrist_relative)
        
        if not wrist_positions:
            return 50.0, self.create_metric("range_of_motion", 50.0), []
        
        avg_wrist_position = np.mean(wrist_positions)
        # Ideal: wrist at or slightly below shoulder (0.02 to 0.05)
        ideal_position = 0.03
        if avg_wrist_position >= ideal_position - 0.02:
            score = 100.0
        elif avg_wrist_position >= ideal_position - 0.05:
            score = 70.0 + ((avg_wrist_position - (ideal_position - 0.05)) / 0.03) * 30.0
        else:
            score = max(0, (avg_wrist_position / (ideal_position - 0.05)) * 70.0)
        
        score = min(100, max(0, score))
        metric = self.create_metric("range_of_motion", score, value=round(avg_wrist_position, 3))
        
        feedback = []
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent range of motion — bar pulled to chest.", "range_of_motion"))
        elif score < 60:
            feedback.append(self.create_beginner_feedback(
                "critical",
                "range_of_motion",
                "In lat pulldowns, you tend to stop short of a full pull (not bringing the bar down to your chest) and sometimes use your body weight to jerk the bar down. This means your lats aren't fully engaged through the motion.",
                [
                    "Pull the bar to your upper chest each rep. Imagine pulling your shoulder blades down and back as you do so",
                    "At the bottom of the rep, you should feel a strong squeeze in your armpit area/back, and the bar should be near chin or collarbone level",
                    "Avoid rocking way back. A slight lean is okay, but don't turn it into a row by swinging your body",
                    "Control the ascent. Let the bar rise back up slowly, fully extending your arms overhead. You should feel a stretch in your lats at the top"
                ],
                "You should feel a strong squeeze in your back and armpit area when the bar is at your chest.",
                "Do not stop halfway. Pull the bar all the way to your upper chest.",
                "Film from the side. The bar should touch your upper chest or be at chin level at the bottom of each rep."
            ))
        else:
            feedback.append(self.create_beginner_feedback(
                "warning",
                "range_of_motion",
                "Your range of motion can be improved for better lat muscle engagement.",
                [
                    "Pull the bar to your upper chest each rep",
                    "Feel a strong squeeze in your back at the bottom",
                    "Control the ascent — don't let the bar yank you up"
                ],
                "You should feel a strong squeeze in your back when the bar is at your chest.",
                "Do not stop short. Pull the bar all the way to your chest.",
                "Check that the bar reaches your upper chest or chin level at the bottom."
            ))
        
        return score, metric, feedback






