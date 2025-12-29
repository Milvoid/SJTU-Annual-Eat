package main

import (
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"time"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/app"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/dialog"
	"fyne.io/fyne/v2/layout"
	"fyne.io/fyne/v2/widget"

	analysispkg "SJTU-Annual-Eat/analysis"
	"SJTU-Annual-Eat/getdata"
)

// RunUI 启动基于 Fyne 的图形界面，流程与命令行版本一致：
// 先打开授权链接登录，再粘贴重定向 URL，最后自动换取 token 并拉取消费数据。
func RunUI() {
	authorizationURL, err := getdata.BuildAuthorizationURL("")
	if err != nil {
		// 如果连授权链接都构造不了，直接降级打印错误
		fmt.Printf("构造授权链接失败: %v\n", err)
		return
	}

	a := app.New()
	a.Settings().SetTheme(chineseTheme{})
	w := a.NewWindow("SJTU Annual Eat - 获取思源码消费数据")
	w.Resize(fyne.NewSize(420, 520))

	logArea := widget.NewMultiLineEntry()
	logArea.SetPlaceHolder("日志输出...")
	logArea.Disable()
	logScroll := container.NewVScroll(logArea)
	logScroll.SetMinSize(fyne.NewSize(0, 140))

	statusLabel := widget.NewLabel("")

	beginDefault := time.Date(2025, 1, 1, 0, 0, 0, 0, time.Local)
	today := time.Now()

	beginEntry := widget.NewEntry()
	beginEntry.SetPlaceHolder("YYYY-MM-DD")
	beginEntry.SetText(beginDefault.Format("2006-01-02"))

	endEntry := widget.NewEntry()
	endEntry.SetPlaceHolder("YYYY-MM-DD")
	endEntry.SetText(today.Format("2006-01-02"))

	redirectInput := widget.NewEntry()
	redirectInput.SetPlaceHolder("在这里粘贴登录后的完整链接")

	authLinkEntry := widget.NewEntry()
	authLinkEntry.SetText(authorizationURL)
	authLinkEntry.Disable()

	copyButton := widget.NewButton("复制授权链接", func() {
		w.Clipboard().SetContent(authorizationURL)
		statusLabel.SetText("已复制授权链接，粘贴到浏览器打开并登录 jAccount")
	})

	openBrowserBtn := widget.NewButton("在浏览器中打开 ↗", func() {
		u, parseErr := url.Parse(authorizationURL)
		if parseErr != nil {
			statusLabel.SetText(fmt.Sprintf("无法解析授权链接: %v", parseErr))
			return
		}
		if err := fyne.CurrentApp().OpenURL(u); err != nil {
			statusLabel.SetText(fmt.Sprintf("尝试打开浏览器失败: %v", err))
			return
		}
		statusLabel.SetText("已尝试在浏览器打开授权链接")
	})

	runBtn := widget.NewButton("开始获取消费数据", nil)
	reportBtn := widget.NewButton("生成报告", nil)
	reportBtn.Importance = widget.HighImportance

	appendLog := func(msg string) {
		now := time.Now().Format("15:04:05")
		line := fmt.Sprintf("[%s] %s", now, msg)
		if strings.TrimSpace(logArea.Text) == "" {
			logArea.SetText(line)
		} else {
			logArea.SetText(logArea.Text + "\n" + line)
		}
	}

	setStatus := func(msg string) {
		statusLabel.SetText(msg)
	}

	// 主要流程：解析用户粘贴的 URL，换取 token，再拉取消费数据保存到 eat-data.json。
	runBtn.OnTapped = func() {
		go func() {
			runBtn.Disable()
			defer runBtn.Enable()

			rawRedirect := strings.TrimSpace(redirectInput.Text)
			if rawRedirect == "" {
				setStatus("请先粘贴登录完成后的重定向链接")
				return
			}

			appendLog("正在解析重定向链接获取授权码...")
			code, err := extractCodeFromRedirect(rawRedirect)
			if err != nil {
				setStatus(err.Error())
				appendLog(err.Error())
				dialog.ShowError(err, w)
				return
			}
			appendLog("已获取授权码，正在换取访问令牌...")

			token, err := getdata.GetAccessToken(code)
			if err != nil {
				setStatus("获取访问令牌失败")
				appendLog(err.Error())
				dialog.ShowError(err, w)
				return
			}
			setStatus("访问令牌获取成功")

			begin := time.Date(2025, 1, 1, 0, 0, 0, 0, time.Local).Unix()
			end := time.Now().Unix()

			parseDate := func(s string) (time.Time, error) {
				return time.ParseInLocation("2006-01-02", strings.TrimSpace(s), time.Local)
			}

			if b, err := parseDate(beginEntry.Text); err == nil {
				begin = time.Date(b.Year(), b.Month(), b.Day(), 0, 0, 0, 0, time.Local).Unix()
			} else {
				err := fmt.Errorf("开始日期格式不正确，应为 YYYY-MM-DD")
				setStatus(err.Error())
				appendLog(err.Error())
				dialog.ShowError(err, w)
				return
			}
			if e, err := parseDate(endEntry.Text); err == nil {
				// 结束日期设到当天末尾，方便覆盖整天
				end = time.Date(e.Year(), e.Month(), e.Day(), 23, 59, 59, 0, time.Local).Unix()
			} else {
				err := fmt.Errorf("结束日期格式不正确，应为 YYYY-MM-DD")
				setStatus(err.Error())
				appendLog(err.Error())
				dialog.ShowError(err, w)
				return
			}

			if begin > end {
				err := fmt.Errorf("开始日期不能晚于结束日期")
				setStatus(err.Error())
				appendLog(err.Error())
				dialog.ShowError(err, w)
				return
			}
			appendLog(fmt.Sprintf("拉取消费数据，时间区间 [%s ~ %s]",
				time.Unix(begin, 0).Format("2006-01-02 15:04:05"),
				time.Unix(end, 0).Format("2006-01-02 15:04:05")))

			_, err = getdata.FetchEatData(token.AccessToken, begin, end, "eat-data.json")
			if err != nil {
				setStatus("消费数据获取失败")
				appendLog(err.Error())
				dialog.ShowError(err, w)
				return
			}

			setStatus("完成：已保存到 eat-data.json")
			appendLog("成功获取消费数据并保存到 eat-data.json")
			dialog.ShowInformation("完成", "消费数据已保存到 eat-data.json", w)
		}()
	}

	reportBtn.OnTapped = func() {
		go func() {
			reportBtn.Disable()
			defer reportBtn.Enable()

			dataPath := "eat-data.json"
			outPath := "report-generated.html"

			if _, err := os.Stat(dataPath); err != nil {
				msg := "未找到 eat-data.json，请先拉取消费数据"
				setStatus(msg)
				dialog.ShowError(fmt.Errorf(msg), w)
				return
			}

			appendLog("开始生成报告...")
			output, err := analysispkg.GenerateReport(dataPath, reportTemplate, outPath)
			if err != nil {
				setStatus("生成报告失败")
				appendLog(err.Error())
				dialog.ShowError(err, w)
				return
			}

			abs, _ := filepath.Abs(output)
			setStatus("报告已生成")
			appendLog("报告已生成：" + abs)
			dialog.ShowInformation("报告已生成", fmt.Sprintf("报告文件：%s", abs), w)
		}()
	}

	content := container.NewVBox(
		widget.NewLabel("1. 打开授权链接，在浏览器中登录 jAccount"),
		container.NewHBox(copyButton, openBrowserBtn),
		authLinkEntry,
		widget.NewLabel("2. 粘贴登陆后跳转的完整链接"),
		redirectInput,
		widget.NewLabel("3. 消费数据时间范围"),
		container.New(layout.NewFormLayout(),
			widget.NewLabel("开始日期"),
			beginEntry,
			widget.NewLabel("结束日期"),
			endEntry,
		),
		runBtn,
		widget.NewLabel("4. 生成报告"),
		reportBtn,
		statusLabel,
		widget.NewSeparator(),
		widget.NewLabel("运行日志"),
		logScroll,
	)

	w.SetContent(content)
	w.ShowAndRun()
}

// extractCodeFromRedirect 从重定向后的完整 URL 中解析 code。
func extractCodeFromRedirect(raw string) (string, error) {
	parsed, err := url.Parse(strings.TrimSpace(raw))
	if err != nil {
		return "", fmt.Errorf("无法解析 URL: %w", err)
	}

	code := parsed.Query().Get("code")
	if code == "" {
		return "", fmt.Errorf("URL 中未找到 code 参数，请确认复制的是完整跳转链接")
	}

	return code, nil
}
