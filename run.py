from tkinter import filedialog
from praatio import textgrid
import tkinter as tk
import pandas as pd
import argparse
import shutil
import os
import utils
import dtw


DICTIONARY = "english_us_arpa"
ACOUSTIC_MODEL = "english_us_arpa"


'''
download pretrained model if needed
 	mfa model download acoustic english_us_arpa
 	mfa model download dictionary english_us_arpa
'''

def main():

	##############################################################################
	##############################################################################
	########## FORCE ALIGNMENT #########################################################

	parser = argparse.ArgumentParser(
		description="Force Align a .wav file with a .txt transcript, then produce a .srt."
	)
	parser.add_argument("--wav_file", type=str, default="data/test.wav",
						help="Path to the input .wav file (default: data/test.wav)")
	parser.add_argument("--trans_file", type=str, default="data/test.txt",
						help="Path to the input transcript .txt file (default: data/test.txt)")
	parser.add_argument("--output_dir", type=str, default="result",
						help="Path to the output directory")
	parser.add_argument("--debug", action="store_true", help="啟用除錯模式")

	args = parser.parse_args()


	wav_file = args.wav_file
	trans_file = args.trans_file
	DEBUG = args.debug
	dir_name = "result-[" + os.path.splitext(os.path.basename(wav_file))[0] + "]"
	output_dir = args.output_dir
	output_dir = os.path.join(output_dir, dir_name)
	debug_dir = os.path.join(output_dir, 'metadata')
	os.makedirs(output_dir, exist_ok=True)
	os.makedirs(debug_dir, exist_ok=True)
	stage_id = 0

	# align wav and transcription
	align_one_cmd, output_file = utils.get_MFA_align_one_cmd(wav_file, trans_file, output_dir, DICTIONARY, ACOUSTIC_MODEL)
	utils.shell(align_one_cmd)



	##############################################################################
	##############################################################################
	########## SRT GENERATION ####################################################

	textgrid_file = output_file
	output_trans =  trans_file  

	# get aligned textGrid data
	tg = textgrid.openTextgrid(textgrid_file, False)
	data = tg.getTier("words").entries
	output = pd.DataFrame([(start, end, word) for (start, end, word) in data],
				columns = ['start','end','word'])
	if DEBUG:
		shutil.copy(textgrid_file, os.path.join(debug_dir, f"{stage_id}-textGrid.TextGrid"))
		os.remove(textgrid_file)
		output_csv_file = os.path.join(debug_dir, f"{stage_id}-textGrid.csv")
		output.to_csv(output_csv_file, index=False, encoding='utf-8')
		print(f'除錯模式開啟，儲存FORCE ALIGNMENT結果為{output_csv_file}')
	else:
		os.remove(textgrid_file)
	stage_id += 1


	# parse transcript txt file
	mfa_wordseq = output["word"].tolist()
	trans_wordseq = []
	ori_transcript = {
		"sentence" : [],
		"end_index": [],
	}
	with open(output_trans, "r", encoding="utf-8") as file:
		cur = 0
		for line in file:
			ls = line.strip()
			if ls:
				ori_transcript["sentence"].append(ls)
				trans_wordseq += ls.split(' ')
				ori_transcript["end_index"].append(len(trans_wordseq) - 1)


	distance, path = dtw.align_forced_t1(trans_wordseq, mfa_wordseq)

	if DEBUG:
		# save text alignment result
		align_txt = []
		for (i, j) in path:
			tmp = f"T1[{i:2}] = {trans_wordseq[i]:>4}   <-->   T2[{j:2}] = {mfa_wordseq[j]:>4}"
			align_txt.append(tmp)
		align_txt = '\n'.join(align_txt)
		align_file_path = os.path.join(debug_dir, f"{stage_id}-align_result.txt")
		with open(align_file_path, "w", encoding="utf-8") as file:
			file.write(align_txt)
		print(f'除錯模式開啟，儲存文本對齊結果為{align_file_path}')
	stage_id += 1


	# timestamp generation
	trans_cor = {}
	for trans_id, mfa_id in path:
		trans_cor[trans_id] = []
	for trans_id, mfa_id in path:
		trans_cor[trans_id].append(mfa_id)

	result_txt = []
	results = []
	start_id = 0
	for sent_id in range(len(ori_transcript["sentence"])):
		ids = [start_id, ori_transcript['end_index'][sent_id]]
		tmp_result = {
			"sentence": ''.join(ori_transcript["sentence"][sent_id]),
			"start": output['start'].tolist()[trans_cor[ids[0]][0]],
			"end": output['end'].tolist()[trans_cor[ids[1]][-1]]
		}
		result_txt.append(f'sentence: {ori_transcript["sentence"][sent_id]}')
		for trans_id, key in zip(ids, ['start', 'end']):
			for mfa_id in trans_cor[trans_id]:
				if trans_wordseq[trans_id] == mfa_wordseq[mfa_id]:
					tmp_result[key] = output[key].tolist()[mfa_id]
					break
			result_txt.append(f'	{key}: <trans>:{trans_wordseq[trans_id]}  <mfa>:{mfa_wordseq[mfa_id]} <time>:{tmp_result[key]}')
		start_id = ori_transcript['end_index'][sent_id] + 1
		tmp_result['start'] = utils.s2ms(tmp_result['start'])
		tmp_result['end'] = utils.s2ms(tmp_result['end'])
		results.append(tmp_result)

	if DEBUG:
		# save timestamp result
		result_txt = '\n'.join(result_txt)
		result_txt_file_path = os.path.join(debug_dir, f"{stage_id}-timestamp.txt")
		with open(result_txt_file_path, "w", encoding="utf-8") as file:
			file.write(result_txt)
		print(f'除錯模式開啟，儲存時間戳為{align_file_path}')
	stage_id += 1

	# save timestamp to srt
	output_df = pd.DataFrame(results)
	csv_file_path = os.path.join(output_dir, f"{stage_id}-result.csv")
	output_df.to_csv(csv_file_path, index=False, encoding='utf-8')
	srt_file_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(wav_file))[0]}.srt")
	utils.convert_to_srt(csv_file_path, srt_file_path)
	if DEBUG:
		shutil.copy(csv_file_path, os.path.join(debug_dir, os.path.basename(csv_file_path)))
		os.remove(csv_file_path)
	else:
		os.remove(csv_file_path)

if __name__ == "__main__":
    main()




