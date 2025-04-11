import os
import sys
import datetime
import platform
import psutil
import time
import re

sys.set_int_max_str_digits(0) #整数文字列制限解除

def get_system_info():
    """システム情報取得"""
    info = {}
    info['cpu'] = platform.processor()
    info['cpu_count'] = psutil.cpu_count(logical=True)
    info['physical_cpu_count'] = psutil.cpu_count(logical=False)
    memory = psutil.virtual_memory()
    info['total_memory'] = f"{memory.total / (1024 ** 3):.2f} GB"
    info['available_memory'] = f"{memory.available / (1024 ** 3):.2f} GB"
    info['python_version'] = platform.python_version()
    info['python_implementation'] = platform.python_implementation()
    info['os'] = platform.system()
    info['os_version'] = platform.version()
    info['os_release'] = platform.release()
    
    return info

def format_time(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{seconds:.3f}"

def extract_number_from_filename(filename):
    base_name = os.path.splitext(filename)[0]
    match = re.search(r'(\d+)$', base_name)
    if match:
        return int(match.group(1))
    return None

def check_file_content(file_path, n):
    try:
        with open(file_path, 'r') as f:
            content = f.read().strip()
        expected_value = str(2 ** n)
        if expected_value == content:
            return True, expected_value, content
        else:
            return False, expected_value, content
    except Exception as e:
        return False, "エラー", str(e)

def check_files(folder_path, output_file, include_subdirs=True):
    if not os.path.isdir(folder_path):
        print(f"エラー: {folder_path} は有効なディレクトリではありません。")
        return False
    
    start_time = time.time()
    all_correct = True
    files_checked = 0
    ok_numbers = []
    ng_numbers = []
    file_paths = []

    if include_subdirs:
        for root, _, files in os.walk(folder_path):
            for filename in files:
                if filename.endswith('.txt'):
                    file_paths.append(os.path.join(root, filename))
    else:
        for filename in os.listdir(folder_path):
            if filename.endswith('.txt'):
                file_paths.append(os.path.join(folder_path, filename))
    
    for file_path in file_paths:
        filename = os.path.basename(file_path)
        try:
            n = extract_number_from_filename(filename)
            if n is None:
                rel_path = os.path.relpath(file_path, folder_path)
                print(f"スキップ: {rel_path} は数値として解釈できないファイル名です。")
                continue
            is_valid, expected, actual = check_file_content(file_path, n)
            rel_path = os.path.relpath(file_path, folder_path)
            if is_valid:
                print(f"ファイル {rel_path} は正しいです")
                ok_numbers.append((n, rel_path))
            else:
                print(f"エラー: ファイル {rel_path} の内容が一致しません。")
                print(f"  期待値: 2^{n} = {expected[:50]}...（省略）")
                print(f"  実際値: {actual[:50]}...（省略）")
                ng_numbers.append((n, rel_path))
                all_correct = False

            files_checked += 1
        
        except Exception as e:
            rel_path = os.path.relpath(file_path, folder_path)
            print(f"エラー: {rel_path} の処理中に問題が発生しました: {str(e)}")
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    if files_checked == 0:
        print("警告: チェックできるテキストファイルが見つかりませんでした。")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("チェックできるテキストファイルが見つかりませんでした。\n")
        return False
    
    system_info = get_system_info()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# 検証実行日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# フォルダパス: {os.path.abspath(folder_path)}\n")
        f.write(f"# サブディレクトリ含む: {'はい' if include_subdirs else 'いいえ'}\n")
        f.write(f"# 実行時間: {format_time(execution_time)} (合計 {files_checked} ファイル)\n\n")
        f.write("# システム情報\n")
        f.write(f"# CPU: {system_info['cpu']} ({system_info['physical_cpu_count']}物理コア, {system_info['cpu_count']}論理コア)\n")
        f.write(f"# メモリ: 合計 {system_info['total_memory']}, 利用可能 {system_info['available_memory']}\n")
        f.write(f"# OS: {system_info['os']} {system_info['os_release']} ({system_info['os_version']})\n")
        f.write(f"# Python: {system_info['python_implementation']} {system_info['python_version']}\n\n")
        f.write(f"正常✅: {len(ok_numbers)}件\n")
        f.write(f"異常×: {len(ng_numbers)}件\n")
        if ng_numbers:
            f.write("\n以下異常と判定された数です (数値:ファイルパス)\n")
            for n, path in sorted(ng_numbers, key=lambda x: x[0]):  #ソート
                f.write(f"{n}: {path}\n")
    
    print(f"\n結果は {output_file} に保存されました。")
    return all_correct

folder_path = "."
output_file = "check_results.txt"
include_subdirs = True

print(f"フォルダ '{folder_path}' 内のファイルをチェックします...")
if include_subdirs:
    print("サブディレクトリも含めてチェックします")
result = check_files(folder_path, output_file, include_subdirs)

if result:
    print("すべてのファイルが正しく検証されました。")
else:
    print("一部またはすべてのファイルに問題があります。")
