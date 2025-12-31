#!/usr/bin/env python3
"""
End-to-end test script for TrueForm AI backend pipeline.
Tests all endpoints and reports status.
"""

import sys
import os
import time
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any

BASE_URL = "http://localhost:8000"
HEALTH_ENDPOINT = f"{BASE_URL}/health"
SPORTS_ENDPOINT = f"{BASE_URL}/api/v1/sports"
UPLOAD_ENDPOINT = f"{BASE_URL}/api/v1/upload"
STATUS_ENDPOINT_TEMPLATE = f"{BASE_URL}/api/v1/status/{{video_id}}"
RESULTS_ENDPOINT_TEMPLATE = f"{BASE_URL}/api/v1/status/results/{{video_id}}"

# Test video path (create dummy if needed)
TEST_VIDEO_PATH = "test.mp4"
DUMMY_VIDEO_SIZE = 1024 * 100  # 100KB dummy file


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_success(message: str):
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")


def print_error(message: str):
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")


def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")


def print_info(message: str):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.RESET}")


def print_section(title: str):
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")


def check_server_health() -> bool:
    """Test 1: Check if FastAPI server is running"""
    print_section("Test 1: Server Health Check")
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                print_success(f"Server is running: {data}")
                return True
            else:
                print_error(f"Server returned unexpected status: {data}")
                return False
        else:
            print_error(f"Server returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to server at {BASE_URL}")
        print_info("Make sure the server is running: uvicorn app.main:app --reload --port 8000")
        return False
    except Exception as e:
        print_error(f"Error checking server health: {str(e)}")
        return False


def check_sports_endpoint() -> bool:
    """Test 2: Check sports endpoint"""
    print_section("Test 2: Sports Endpoint")
    try:
        response = requests.get(SPORTS_ENDPOINT, timeout=5)
        if response.status_code == 200:
            sports = response.json()
            print_success(f"Retrieved {len(sports)} sports")
            for sport in sports:
                print_info(f"  - {sport.get('name')} (ID: {sport.get('id')})")
                if sport.get('requires_exercise_type'):
                    ex_types = sport.get('exercise_types', [])
                    print_info(f"    Exercise types: {len(ex_types)}")
            return True
        else:
            print_error(f"Sports endpoint returned status code: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error checking sports endpoint: {str(e)}")
        return False


def create_dummy_video() -> Optional[str]:
    """Create a minimal dummy video file for testing"""
    dummy_path = "test_dummy.mp4"
    if os.path.exists(TEST_VIDEO_PATH):
        return TEST_VIDEO_PATH
    
    print_warning(f"Test video '{TEST_VIDEO_PATH}' not found")
    print_info("Creating dummy video file (this won't process correctly, but tests upload)")
    
    # Create a minimal file that looks like a video (but won't actually work)
    try:
        with open(dummy_path, "wb") as f:
            f.write(b'\x00' * DUMMY_VIDEO_SIZE)
        return dummy_path
    except Exception as e:
        print_error(f"Could not create dummy video: {e}")
        return None


def upload_test_video() -> Optional[str]:
    """Test 3: Upload a test video"""
    print_section("Test 3: Video Upload")
    
    video_path = create_dummy_video()
    if not video_path or not os.path.exists(video_path):
        print_error("No test video available, skipping upload test")
        return None
    
    try:
        with open(video_path, "rb") as f:
            files = {"video": (os.path.basename(video_path), f, "video/mp4")}
            data = {
                "sport": "basketball",
                "exercise_type": "jumpshot"
            }
            
            print_info(f"Uploading {video_path}...")
            response = requests.post(UPLOAD_ENDPOINT, files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                video_id = result.get("video_id")
                print_success(f"Video uploaded successfully")
                print_info(f"  Video ID: {video_id}")
                print_info(f"  Filename: {result.get('filename')}")
                print_info(f"  Sport: {result.get('sport')}")
                print_info(f"  Exercise Type: {result.get('exercise_type')}")
                return video_id
            else:
                print_error(f"Upload failed with status {response.status_code}")
                print_error(f"Response: {response.text}")
                return None
    except Exception as e:
        print_error(f"Error uploading video: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def poll_status(video_id: str, max_attempts: int = 30, interval: int = 2) -> bool:
    """Test 4: Poll status endpoint until completed"""
    print_section("Test 4: Status Polling")
    
    print_info(f"Polling status for video_id: {video_id}")
    print_info(f"Max attempts: {max_attempts}, Interval: {interval}s")
    
    for attempt in range(1, max_attempts + 1):
        try:
            url = STATUS_ENDPOINT_TEMPLATE.format(video_id=video_id)
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get("status", "unknown")
                progress = status_data.get("progress", 0)
                
                print_info(f"Attempt {attempt}/{max_attempts}: Status={status}, Progress={progress}%")
                
                if status == "completed":
                    print_success(f"Processing completed in {attempt * interval} seconds")
                    print_info(f"  Analysis ID: {status_data.get('analysis_id')}")
                    return True
                elif status == "error":
                    error_msg = status_data.get("error", "Unknown error")
                    print_error(f"Processing failed: {error_msg}")
                    return False
                elif status in ["queued", "processing"]:
                    time.sleep(interval)
                else:
                    print_warning(f"Unknown status: {status}")
                    time.sleep(interval)
            elif response.status_code == 404:
                print_error(f"Video not found (404)")
                return False
            else:
                print_error(f"Status endpoint returned {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print_error(f"Error polling status: {str(e)}")
            if attempt < max_attempts:
                time.sleep(interval)
            else:
                return False
    
    print_warning(f"Status polling timed out after {max_attempts * interval} seconds")
    return False


def check_results(video_id: str) -> bool:
    """Test 5: Check if results are generated"""
    print_section("Test 5: Results Endpoint")
    
    try:
        url = RESULTS_ENDPOINT_TEMPLATE.format(video_id=video_id)
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            results = response.json()
            print_success("Results retrieved successfully")
            print_info(f"  Analysis ID: {results.get('analysis_id')}")
            print_info(f"  Sport: {results.get('sport')}")
            print_info(f"  Overall Score: {results.get('overall_score')}")
            print_info(f"  Metrics Count: {len(results.get('metrics', []))}")
            print_info(f"  Feedback Count: {len(results.get('feedback', []))}")
            print_info(f"  Strengths: {len(results.get('strengths', []))}")
            print_info(f"  Weaknesses: {len(results.get('weaknesses', []))}")
            
            # Print sample metrics
            metrics = results.get('metrics', [])
            if metrics:
                print_info("\nSample Metrics:")
                for metric in metrics[:5]:
                    print_info(f"  - {metric.get('name')}: {metric.get('score')}/100")
            
            return True
        elif response.status_code == 404:
            print_error("Results not found (404)")
            return False
        else:
            print_error(f"Results endpoint returned {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error checking results: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def cleanup_dummy_file():
    """Remove dummy video file if created"""
    dummy_path = "test_dummy.mp4"
    if os.path.exists(dummy_path):
        try:
            os.remove(dummy_path)
            print_info(f"Cleaned up dummy file: {dummy_path}")
        except:
            pass


def main():
    print_section("TrueForm AI - End-to-End Pipeline Test")
    print_info(f"Testing against: {BASE_URL}")
    
    results = {
        "health_check": False,
        "sports_endpoint": False,
        "video_upload": False,
        "status_polling": False,
        "results_check": False,
    }
    
    # Test 1: Health check
    results["health_check"] = check_server_health()
    if not results["health_check"]:
        print_error("\nServer is not running. Exiting tests.")
        print_info("Start server with: uvicorn app.main:app --reload --port 8000")
        sys.exit(1)
    
    # Test 2: Sports endpoint
    results["sports_endpoint"] = check_sports_endpoint()
    
    # Test 3: Upload video
    video_id = upload_test_video()
    results["video_upload"] = video_id is not None
    
    # Test 4 & 5: Only if upload succeeded
    if video_id:
        results["status_polling"] = poll_status(video_id)
        if results["status_polling"]:
            results["results_check"] = check_results(video_id)
    
    # Cleanup
    cleanup_dummy_file()
    
    # Final Summary
    print_section("Test Summary")
    for test_name, passed in results.items():
        if passed:
            print_success(f"{test_name.replace('_', ' ').title()}: PASSED")
        else:
            print_error(f"{test_name.replace('_', ' ').title()}: FAILED")
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n{Colors.BOLD}Results: {passed_count}/{total_count} tests passed{Colors.RESET}\n")
    
    if passed_count == total_count:
        print_success("All tests passed! 🎉")
        sys.exit(0)
    else:
        print_error("Some tests failed. Check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()






<<<<<<< HEAD


=======
>>>>>>> 3cec07eb73eb7a9d41527c45e27aa974b9b882ec
