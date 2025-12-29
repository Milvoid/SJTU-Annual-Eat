package getdata

import (
	"bufio"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"strings"
	"time"
)

// ---- 配置部分 ----

const (
	authorizationURL = "https://jaccount.sjtu.edu.cn/oauth2/authorize"
	apiURL           = "https://api.sjtu.edu.cn/v1/unicode/transactions"
	tokenURL         = "https://jaccount.sjtu.edu.cn/oauth2/token"
	redirectURI      = "https://net.sjtu.edu.cn"

	// 使用交我办的数据
	clientID     = ""
	clientSecret = ""
)

// ---- 类型定义 ----

// OAuth 拿到的 token 响应
type TokenResponse struct {
	AccessToken string `json:"access_token"`
	TokenType   string `json:"token_type"`
	ExpiresIn   int    `json:"expires_in"`
	Scope       string `json:"scope"`
}

// ---- 授权相关 ----

// BuildAuthorizationURL 构造授权 URL
func BuildAuthorizationURL(state string) (string, error) {
	params := url.Values{}
	params.Set("response_type", "code")
	params.Set("client_id", clientID)
	params.Set("redirect_uri", redirectURI)
	params.Set("scope", "")
	params.Set("state", state)

	u, err := url.Parse(authorizationURL)
	if err != nil {
		return "", err
	}
	u.RawQuery = params.Encode()
	return u.String(), nil
}

// 完全复刻 Python：打印 URL，让你去浏览器登录，
// 然后在命令行粘贴重定向后的完整链接，解析出 code。
func GetAuthorizationCodeInteractive() (string, error) {
	authURL, err := BuildAuthorizationURL("")
	if err != nil {
		return "", err
	}

	fmt.Println("\n请在浏览器中打开以下链接并登录:\n")
	fmt.Println(authURL)
	fmt.Println("\n登录完毕后，请稍等片刻至跳转到网络信息中心页面")
	fmt.Println("此时复制浏览器地址栏中的完整链接，并粘贴到这里，按回车确认:\n")

	reader := bufio.NewReader(os.Stdin)
	redirectResponse, err := reader.ReadString('\n')
	if err != nil {
		return "", err
	}
	redirectResponse = strings.TrimSpace(redirectResponse)

	parsed, err := url.Parse(redirectResponse)
	if err != nil {
		return "", fmt.Errorf("无法解析你粘贴的 URL: %w", err)
	}

	q := parsed.Query()
	code := q.Get("code")
	if code == "" {
		return "", errors.New("没有在 URL 中找到 code 参数，请确认复制的是完整重定向后的链接")
	}

	return code, nil
}

// GetAccessToken 使用授权码换取 access_token（对应 Python get_access_token）
func GetAccessToken(authorizationCode string) (*TokenResponse, error) {
	form := url.Values{}
	form.Set("grant_type", "authorization_code")
	form.Set("code", authorizationCode)
	form.Set("redirect_uri", redirectURI)

	req, err := http.NewRequest("POST", tokenURL, strings.NewReader(form.Encode()))
	if err != nil {
		return nil, err
	}

	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	req.SetBasicAuth(clientID, clientSecret)

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := ioReadAllLimit(resp.Body, 4096)
		return nil, fmt.Errorf("获取令牌失败: 状态码=%d, 响应=%s", resp.StatusCode, body)
	}

	var token TokenResponse
	if err := json.NewDecoder(resp.Body).Decode(&token); err != nil {
		return nil, err
	}

	if token.AccessToken == "" {
		return nil, errors.New("返回中没有 access_token 字段")
	}

	fmt.Println("\n成功获取访问令牌(Access Token):")
	fmt.Println(token.AccessToken)
	fmt.Println()

	return &token, nil
}

// ---- 消费数据获取部分 ----

// FetchEatData 拉取消费数据，并可选保存到 JSON 文件。
// begin/end 采用 Unix 时间戳（秒）；如果 endUnix <= 0，则不带 endDate 参数。
// filePath 为空字符串时不写文件；非空则类似 Python 版写入对应 JSON。
func FetchEatData(accessToken string, beginUnix, endUnix int64, filePath string) (map[string]any, error) {
	params := url.Values{}
	params.Set("access_token", accessToken)
	params.Set("channel", "")
	params.Set("start", "0")
	params.Set("beginDate", strconv.FormatInt(beginUnix, 10))
	params.Set("status", "")
	if endUnix > 0 {
		params.Set("endDate", strconv.FormatInt(endUnix, 10))
	}

	u, err := url.Parse(apiURL)
	if err != nil {
		return nil, err
	}
	u.RawQuery = params.Encode()

	fmt.Println("正在获取消费数据...")
	fmt.Println("URL:", u.String())
	resp, err := http.Get(u.String())
	if err != nil {
		return nil, fmt.Errorf("请求过程中发生错误，请检查网络及代理设置: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := ioReadAllLimit(resp.Body, 4096)
		return nil, fmt.Errorf("请求失败，状态码: %d, 错误信息: %s", resp.StatusCode, body)
	}

	// 用 map[string]any 接收完整 JSON，避免丢字段
	var apiResp map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&apiResp); err != nil {
		return nil, err
	}

	// 检查 errno 字段（和 Python 一样只看 errno 是否为 0）
	if v, ok := apiResp["errno"]; ok {
		if errno, ok2 := v.(float64); ok2 && int(errno) != 0 {
			// 防止泄露 client_id/client_secret，这里只打印 errno
			return nil, fmt.Errorf("API 错误: errno=%d", int(errno))
		}
	}

	fmt.Println("消费数据获取成功")

	// 和 Python 一样，把整个响应 JSON 写到文件里
	if filePath != "" {
		if err := saveJSONPretty(filePath, apiResp); err != nil {
			return nil, fmt.Errorf("消费数据已获取，但写入文件失败: %w", err)
		}
		fmt.Printf("\n消费数据已保存到 %s\n", filePath)
	}

	return apiResp, nil
}

// ---- 辅助函数 ----

// saveJSONPretty 把 v 以缩进 JSON 写入文件（等价 Python 的 indent=4）
func saveJSONPretty(filename string, v any) error {
	f, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer f.Close()

	enc := json.NewEncoder(f)
	enc.SetIndent("", "    ")
	return enc.Encode(v)
}

// ioReadAllLimit：简单限制一下错误输出长度，避免出特别长的 HTML
func ioReadAllLimit(r io.Reader, limit int64) (string, error) {
	if limit <= 0 {
		limit = 4096
	}
	lr := &io.LimitedReader{R: r, N: limit}
	b, err := io.ReadAll(lr)
	return string(b), err
}

// 一个简单的 helper：给你从 time.Time 直接转 Unix 秒
func UnixOf(t time.Time) int64 {
	return t.Unix()
}
