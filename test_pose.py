import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.pose_estimator import PoseEstimator
import json

def test_pose_estimation(video_path: str = "test.mp4"):
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' not found.")
        print("Please provide a test video file or update the path.")
        return
    
    print(f"Processing video: {video_path}")
    estimator = PoseEstimator()
    
    metadata = estimator.get_video_metadata(video_path)
    print(f"\nVideo Metadata:")
    print(f"  FPS: {metadata.get('fps', 0):.2f}")
    print(f"  Frame Count: {metadata.get('frame_count', 0)}")
    print(f"  Resolution: {metadata.get('width', 0)}x{metadata.get('height', 0)}")
    print(f"  Duration: {metadata.get('duration', 0):.2f}s")
    
    print(f"\nExtracting pose data...")
    pose_data = estimator.process_video(video_path)
    
    print(f"Extracted {len(pose_data)} frames with pose data")
    
    if pose_data:
        sample_frame = pose_data[0]
        print(f"\nSample Frame Data:")
        print(f"  Landmarks: {len(sample_frame.get('landmarks', {}))} detected")
        print(f"  Joint Angles:")
        for joint, angle in sample_frame.get('angles', {}).items():
            print(f"    {joint}: {angle:.2f}°")
        
        if len(pose_data) > 1:
            mid_frame = pose_data[len(pose_data) // 2]
            print(f"\nMid Frame Angles:")
            for joint, angle in mid_frame.get('angles', {}).items():
                print(f"    {joint}: {angle:.2f}°")
    
    output_file = "pose_test_output.json"
    with open(output_file, "w") as f:
        json.dump(pose_data, f, indent=2, default=str)
    print(f"\nPose data saved to: {output_file}")

if __name__ == "__main__":
    video_path = sys.argv[1] if len(sys.argv) > 1 else "test.mp4"
    test_pose_estimation(video_path)






