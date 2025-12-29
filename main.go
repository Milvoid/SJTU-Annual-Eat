package main

import (
	"fmt"
	"log"
	"os"
	"path/filepath"
	"time"

	"SJTU-Annual-Eat/getdata"
)

// SetWorkingDir sets CWD to the directory where the binary is located.
func SetWorkingDir() {
	exePath, err := os.Executable()
	if err != nil {
		return
	}
	dir := filepath.Dir(exePath)
	os.Chdir(dir)
}

func main() {
	// 修改工作目录
	SetWorkingDir()

	if len(os.Args) > 1 && os.Args[1] == "cli" {
		runCLI()
		return
	}

	RunUI()
}

// runCLI 保留命令行方式，便于无图形环境时使用。
func runCLI() {
	// 获取授权码
	code, err := getdata.GetAuthorizationCodeInteractive()
	if err != nil {
		log.Fatalf("获取授权码失败: %v", err)
	}
	fmt.Println("已获取授权码:", code)

	// 用授权码获取 access token
	token, err := getdata.GetAccessToken(code)
	if err != nil {
		log.Fatalf("获取访问令牌失败: %v", err)
	}
	fmt.Println("已获取 Access Token")

	// 设定时间区间
	begin := time.Date(2025, 1, 1, 0, 0, 0, 0, time.Local).Unix()

	end := time.Now().Unix()

	fmt.Printf("准备拉取区间 [%v ~ %v] 的消费数据...\n",
		time.Unix(begin, 0).Format("2006-01-02 15:04:05"),
		time.Unix(end, 0).Format("2006-01-02 15:04:05"))

	// 调用 FetchEatData，保存为 eat-data.json
	_, err = getdata.FetchEatData(token.AccessToken, begin, end, "eat-data.json")
	if err != nil {
		log.Fatalf("获取消费数据失败: %v", err)
	}

	fmt.Println("\n完成：请检查当前目录下的 eat-data.json 文件。")
}
