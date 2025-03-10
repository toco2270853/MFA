from tkinter import filedialog
import tkinter as tk
import pandas as pd
import subprocess
import os

def select_file(prompt, filetype_description, filetype):
	print(prompt)
	root = tk.Tk()
	root.withdraw()
	file_path = filedialog.askopenfilename(
		title=prompt,
		filetypes=[(filetype_description, filetype), ("所有檔案", "*.*")]
	)
	if file_path:
		print(f"選擇的檔案: {file_path}")
		return file_path
	else:
		print("未選擇檔案")
		return None

def select_folder(prompt):
    root = tk.Tk()
    root.withdraw() 
    print(prompt)
    folder_path = filedialog.askdirectory(
        title=prompt
    )
    if folder_path:
        print(f"已選擇的資料夾: {folder_path}")
    else:
        print("未選擇任何資料夾")
    return folder_path

def shell(command, run=True):
	
	if run:
		print('開始執行指令:')
		print(command)
		try:
			# 使用 Popen 執行命令
			process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
			# 實時讀取標準輸出
			for line in process.stdout:
				print(line, end="")  # 即時打印到控制台
			# 等待進程完成
			process.wait()
			if process.returncode == 0:
				print("命令執行成功！")
			else:
				print("命令執行失敗！")
				for line in process.stderr:
					print(line, end="")  # 打印錯誤輸出
		except Exception as e:
			print(f"執行命令時出錯: {e}")
	else:
		print('測試指令為:')
		print(command)
		
			
# MFA Wrapper
def get_MFA_align_one_cmd(wav_file, trans_file, output_dir, DICTIONARY, ACOUSTIC_MODEL, output_type=".TextGrid"):
	# mfa align_one [OPTIONS] SOUND_FILE_PATH TEXT_FILE_PATH DICTIONARY_PATH ACOUSTIC_MODEL_PATH OUTPUT_PATH
	print(f"結果將輸出至{output_dir}")
	base_name = os.path.splitext(os.path.basename(wav_file))[0]
	output_file = os.path.join(output_dir, f"{base_name}{output_type}")
	align_one_cmd = f"mfa align_one {wav_file} {trans_file} {DICTIONARY} {ACOUSTIC_MODEL} {output_file}"
	
	return align_one_cmd, output_file

def s2ms(seconds):
	# output time from second to mm:ss
	hr = seconds // 3600
	minute = seconds // 60 
	sec = seconds % 60 
	ms = seconds * 1000 % 1000
	return f"{int(hr):02}:{int(minute):02}:{int(sec):02},{str(int(ms)).zfill(3)}"

def convert_to_srt(csv_file, srt_file):
	"""
	將 CSV 文件轉換為 SRT 文件。
	:param csv_file: CSV 文件路徑
	:param srt_file: 輸出 SRT 文件路徑
	"""
	# 讀取 CSV 文件
	data = pd.read_csv(csv_file)
	
	# 打開 SRT 文件寫入
	with open(srt_file, "w", encoding="utf-8") as srt:
		for index, row in data.iterrows():
			# SRT 格式：
			# 1
			# 00:00:00,000 --> 00:00:03,000
			# Sentence text
			start_time = row['start']
			end_time = row['end']
			sentence = row['sentence']
			
			srt.write(f"{index + 1}\n")  # SRT 編號
			srt.write(f"{start_time} --> {end_time}\n")  # 時間軸
			srt.write(f"{sentence}\n\n")  # 字幕文本與空行

	print(f"SRT 文件已保存到: {srt_file}")