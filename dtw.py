from fastdtw import fastdtw
import Levenshtein

SPECIAL_TOKENS = {"<eps>", "<unk>", "<noise>", "<sil>", "<spn>"}


def token_cost(t1, t2):
    if t1 == t2: # 完全相同的詞，沒有距離
        return 0
    elif (t1 in SPECIAL_TOKENS) or (t2 in SPECIAL_TOKENS):
        return 1 # 有特殊詞，給較小的懲罰
    else:
        return max(Levenshtein.distance(t1, t2) * 5, 50) # 正常詞不同，使用 Levenshtein 距離

def align_texts_with_fastdtw(seq1, seq2):
    """
    用 fastdtw 對齊兩個「文字序列」(seq1, seq2)。
    seq1, seq2: List[str]
    
    為了避開 fastdtw 將輸入轉成 float array 的限制：
    - 我們傳入 range(len(seq1)), range(len(seq2))
    - 並在 dist 函數裡，透過索引去比較 seq1[i]、seq2[j]
    
    回傳:
      distance:  對齊後的總距離
      path:      對齊路徑 (list of (i, j))
    """
    # 先定義一個「封裝距離函數」：接收索引 i, j，實際比較 seq1[i], seq2[j]
    def index_distance(i, j):
        return token_cost(seq1[int(i)], seq2[int(j)])

    # 使用 fastdtw，輸入分別是 range(len(seq1)) 與 range(len(seq2))，
    # 同時指定 dist=index_distance
    distance, path = fastdtw(range(len(seq1)), range(len(seq2)), dist=index_distance)
    return distance, path

def align_forced_t1(seq1, seq2):
    """
    全局比對:
      - T1 不允許刪除 (成本極大)
      - T2 允許插入 (成本較小)
    回傳:
      (dp[m][n], backtrace) 
        - dp[m][n] 是最小成本
        - backtrace 用來回溯對齊路徑
    """
    m = len(seq1)
    n = len(seq2)

    SKIP_T1_COST = 999999
    SKIP_T2_COST = 2

    # 建立 DP 陣列 + 回溯陣列
    # dp[i][j] 表示 "對齊 T1[:i] 與 T2[:j] 的最小成本"
    dp = [[0]*(n+1) for _ in range(m+1)]
    backtrace = [[(0, 0)]*(n+1) for _ in range(m+1)]  # 儲存 (prev_i, prev_j)

    # 初始化第一欄 (T2=空)
    for i in range(1, m+1):
        dp[i][0] = dp[i-1][0] + SKIP_T1_COST
        backtrace[i][0] = (i-1, 0)

    # 初始化第一列 (T1=空)
    for j in range(1, n+1):
        dp[0][j] = dp[0][j-1] + SKIP_T2_COST
        backtrace[0][j] = (0, j-1)

    # 填 DP 表
    for i in range(1, m+1):
        for j in range(1, n+1):
            # 對角 (match T1[i-1], T2[j-1])
            cost_diag = dp[i-1][j-1] + token_cost(seq1[i-1], seq2[j-1])
            # 跳過 T2 (插入 T2[j-1])
            cost_left = dp[i][j-1] + SKIP_T2_COST
            # 跳過 T1 (刪除 T1[i-1]) -> 極大成本
            cost_up = dp[i-1][j] + SKIP_T1_COST

            best_cost = cost_diag
            best_step = (i-1, j-1)

            if cost_left < best_cost:
                best_cost = cost_left
                best_step = (i, j-1)

            if cost_up < best_cost:
                best_cost = cost_up
                best_step = (i-1, j)

            dp[i][j] = best_cost
            backtrace[i][j] = best_step

    i, j = m, n
    alignment = []
    while i > 0 and j > 0:
        alignment.append((i-1, j-1))
        i, j = backtrace[i][j]

    alignment.reverse()
    return dp[m][n], alignment  


if __name__ == "__main__":
    # T1: 原文本的斷行位置
    T1 = ["a","b","c",
          "d","e","f",
          "g","h","i","j",
          "k","l","m","n","o","p",
          "q","r"]
    
    # T2: Force Alignment 後的文本，可能中間插入或變化一些 token
    T2 = ["a","b","c","1","2","d","e","f","3","4","g","h","i","j","5","k","l","m","n","o","p","q","6","r"]

    # path 會是一串 (i, j) 的對，表示 T1[i] 與 T2[j] 對應
    distance, path = align_texts_with_fastdtw(T1, T2) 
    print("完整回溯路徑: (i, j)")
    for (i, j) in path[:25]:
        print(i,j)
        print(f"T1[{i:2}] = {T1[i]:>4}   <-->   T2[{j:2}] = {T2[j]:>4}")
    
    distance, alignment = align_forced_t1(T1, T2)
    seq1, seq2 = T1, T2
    print("完整回溯路徑: (i, j)")
    for (i, j) in alignment:
        print(i,j)
        print(f"T1[{i:2}] = {T1[i]:>4}   <-->   T2[{j:2}] = {T2[j]:>4}")
