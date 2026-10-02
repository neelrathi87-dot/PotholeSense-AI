import os
import sys
from huggingface_hub import HfApi, login

def main():
    token = sys.argv[1] if len(sys.argv) > 1 else os.getenv("HF_TOKEN")
    if not token:
        print("================================================================")
        print(" 🔑 Hugging Face Token Required")
        print("================================================================")
        print("Get your free Access Token (write permissions) in 10 seconds at:")
        print("👉 https://huggingface.co/settings/tokens")
        print("\nThen run:")
        print("   python deploy_hf.py hf_yourTokenHere")
        print("================================================================")
        return

    print("Authenticating with Hugging Face...")
    try:
        login(token=token, add_to_git_credential=False)
        api = HfApi(token=token)
        user = api.whoami()
        username = user["name"]
        repo_id = f"{username}/potholesense-ai"
        print(f"✓ Logged in as: {username}")
        print(f"✓ Creating/Checking Docker Space: {repo_id}...")
        
        api.create_repo(
            repo_id=repo_id,
            repo_type="space",
            space_sdk="docker",
            private=False,
            exist_ok=True
        )
        
        print(f"✓ Uploading AI Engine, YOLO weights & Dockerfile to Hugging Face...")
        api.upload_folder(
            folder_path=".",
            repo_id=repo_id,
            repo_type="space",
            ignore_patterns=[
                ".git*",
                "node_modules/**",
                "dashboard/**",
                "potholes.db*",
                "*.log",
                "server.pid",
                "cloudflared.exe",
                "active_tunnel_url.txt",
                ".env*",
                "__pycache__/**",
                "offline_buffer/**"
            ]
        )
        
        # Subdomain formatting for HF Spaces
        clean_user = username.lower().replace("_", "-")
        space_url = f"https://{clean_user}-potholesense-ai.hf.space"
        print("\n================================================================")
        print(" 🚀 DEPLOYMENT INITIATED TO HUGGING FACE SPACES!")
        print("================================================================")
        print(f" 🌐 Space Page     : https://huggingface.co/spaces/{repo_id}")
        print(f" 📡 24/7 API Server: {space_url}")
        print(f" 📱 Mobile Patrol  : {space_url}/mobile")
        print(f" 🩺 Health Check   : {space_url}/health")
        print("================================================================")
        print("Hugging Face is building your Docker image now (~2 mins).")
        print("You can close your laptop — it will run 24/7/365 permanently!")
        print("================================================================\n")
    except Exception as e:
        print(f"Deployment error: {e}")

if __name__ == "__main__":
    main()
