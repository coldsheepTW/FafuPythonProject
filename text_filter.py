import re

def replace_words_inside(input_string):
	pattern = re.compile(r'\((.*?)\)')
	tmp = pattern.sub("", input_string)
	pattern = re.compile(r'（.*?）')
	result = pattern.sub("", tmp)
	result = result.replace(':','之')
	return result

def check_first_sentence(input_string):
	result = input_string
	if input_string == "":
		return result

	neg_sentences = ["無法成為耶穌","不是真的耶穌", "不是耶穌", "並非耶穌","聖經中沒有", "聖經中並未", "無法擔任", "無法假設", "AI", "人工智能", "人工智慧","語言模型", "智能助手"]
	# There will be more than 1 sentences

	for s in neg_sentences:
		if s in input_string:
			idx = input_string.find('。')
			if idx != -1:
				result = input_string[idx+1:]
				break

	if result == input_string:
		return result

	return check_first_sentence(result)

def text_filter(content):
	tmp = replace_words_inside(content)
	ans = check_first_sentence(tmp)
	return ans


if __name__ == "__main__":	
	s = "聖經中沒有相關紀載。作為一個人工智能助手，一個AI，語言模型，我不能真正代表耶穌。我要引述我(Jesus)馬太福音11:5說的話（阿呼福音5:11）也就是自說自話"
	ans = text_filter(s)
	print(ans)
