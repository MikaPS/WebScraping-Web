import subprocess

def main():
    try:
        # Run pip install with the full path to requirements.txt
        subprocess.run(['pip', 'install',  'beautifulsoup4==4.12.2'], check=True)
        subprocess.run(['pip', 'install',  'bs4==0.0.1'], check=True)
        subprocess.run(['pip', 'install',  'Flask==3.0.0'], check=True)
        subprocess.run(['pip', 'install',  'requests==2.31.0'], check=True)
        subprocess.run(['pip', 'install',  'Unidecode==1.3.6'], check=True)
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print("Error installing dependencies:", e)
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    main()
