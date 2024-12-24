import subprocess
import os

def execute(file, conn):
    ext = os.path.splitext(file)[-1]
    try:
        if ext == ".py":
            print(f"\033[93mScript python va être executé\033[0m")
            result = subprocess.run(["python", file], capture_output=True, text=True, check=True)
        elif ext == ".c":
            print(f"\033[93mScript C va être executé\033[0m")
            executable = file.replace(".c", "")
            subprocess.run(["gcc", file, "-o", executable], capture_output=True, text=True, check=True)
            result = subprocess.run([f"./{executable}"], capture_output=True, text=True, check=True)
        elif ext == ".cpp":
            print(f"\033[93mScript C++ va être executé\033[0m")
            executable = file.replace(".cpp", "")
            subprocess.run(["g++", file, "-o", executable], capture_output=True, text=True, check=True)
            result = subprocess.run([f"./{executable}"], capture_output=True, text=True, check=True)
        elif ext == ".java":
            print(f"\033[93mScript Java va être executé\033[0m")
            classname = file.replace(".java", "")
            subprocess.run(["javac", file], capture_output=True, text=True, check=True)
            result = subprocess.run(["java", classname], capture_output=True, text=True, check=True)
        else:
            print(f"\033[93mScript ne peut pas être executé\033[0m")
            return "err:lang"
        conn.send("ack".encode())
    except subprocess.CalledProcessError as err:
        error_details=f"Erreur : X" #{err.stderr}
        print(error_details)
        try:
            conn.send(error_details.encode('utf-8'))
        except Exception as send_error:
            print(f"Erreur lors de l'envoi : {send_error}")

    except Exception as err:
        error_details=f"Erreur inattendue : Y" #{err}
        print(error_details)
        conn.send(error_details.encode())
    else:
        print("Sortie standard :")
        print(result.stdout)
        conn.send(result.stdout.encode())
    finally:
        return