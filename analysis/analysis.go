package analysis

import (
	"encoding/json"
	"fmt"
	"html/template"
	"math"
	"os"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"
)

type eatResponse struct {
	Entities []eatEntity `json:"entities"`
	Errno    int         `json:"errno"`
	Error    string      `json:"error"`
}

type eatEntity struct {
	Merchant  string  `json:"merchant"`
	Amount    float64 `json:"amount"`
	OrderTime int64   `json:"orderTime"`
	PayTime   int64   `json:"payTime"`
}

type ReportData struct {
	Year                 int
	TotalAmount          float64
	FirstMealLocation    string
	FirstMealTime        string
	FirstMealAmount      float64
	MaxMealLocation      string
	MaxMealTime          string
	MaxMealAmount        float64
	MostFrequentLocation string
	MostFrequentCount    int
	MostFrequentAmount   float64
	MostSpentLocation    string
	MostSpentAmount      float64
	MostSpentCount       int
	BreakfastCount       int
	LunchCount           int
	DinnerCount          int
	EarliestMealLocation string
	EarliestMealTime     string
	EarliestMealAmount   float64
	PeakMonth            int
	PeakMonthAmount      float64
	ReportJSON           template.JS
	MerchantAmount       map[string]float64
	MonthlyAmount        map[string]float64
	TimeDistribution     map[string]int
}

type chartData struct {
	MerchantAmount   map[string]float64 `json:"MerchantAmount"`
	MonthlyAmount    map[string]float64 `json:"MonthlyAmount"`
	TimeDistribution map[string]int     `json:"TimeDistribution"`
}

var (
	// 与 Python 版保持一致的过滤关键词（去掉车牌号，改为归类为“班车”）
	filterPatterns = []string{
		"电瓶车", "游泳", "核减", "浴室", "教材科", "校医院", "充值",
	}
	filterRegex *regexp.Regexp
	plateRegex  = regexp.MustCompile(`(?i)^沪[0-9A-Z]{4,7}$`)
	cstZone     = time.FixedZone("CST", 8*3600)
)

func init() {
	filterRegex = regexp.MustCompile(stringsJoin(filterPatterns, "|"))
}

// GenerateReport 根据消费数据和模板生成报告 HTML。
// eatPath: 原始消费数据 eat-data.json；tplContent: 模板内容；outPath: 输出 HTML 路径。
func GenerateReport(eatPath string, tplContent []byte, outPath string) (string, error) {
	records, err := loadEatData(eatPath)
	if err != nil {
		return "", err
	}
	if len(records) == 0 {
		return "", fmt.Errorf("消费记录为空，无法生成报告")
	}

	report, err := buildReport(records)
	if err != nil {
		return "", err
	}

	if len(tplContent) == 0 {
		return "", fmt.Errorf("模板内容为空")
	}

	tpl, err := template.New("report").Parse(string(tplContent))
	if err != nil {
		return "", fmt.Errorf("解析模板失败: %w", err)
	}

	outFile, err := os.Create(outPath)
	if err != nil {
		return "", fmt.Errorf("创建输出文件失败: %w", err)
	}
	defer outFile.Close()

	if err := tpl.Execute(outFile, report); err != nil {
		return "", fmt.Errorf("渲染模板失败: %w", err)
	}

	return outPath, nil
}

func loadEatData(path string) ([]eatEntity, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("打开数据文件失败: %w", err)
	}
	defer f.Close()

	var resp eatResponse
	if err := json.NewDecoder(f).Decode(&resp); err != nil {
		return nil, fmt.Errorf("解析 JSON 失败: %w", err)
	}
	if resp.Errno != 0 {
		return nil, fmt.Errorf("数据 errno 非 0: %d %s", resp.Errno, resp.Error)
	}

	var records []eatEntity
	for _, e := range resp.Entities {
		adjAmount := math.Round(-e.Amount*100) / 100 // 与 Python 相同：乘 -1，保留 2 位
		if adjAmount < 0 {
			continue
		}
		merchant := normalizeMerchant(e.Merchant)
		if filterRegex.MatchString(merchant) {
			continue
		}
		// 只保留有效时间
		if e.PayTime == 0 {
			continue
		}
		records = append(records, eatEntity{
			Merchant:  merchant,
			Amount:    adjAmount,
			OrderTime: e.OrderTime,
			PayTime:   e.PayTime,
		})
	}
	return records, nil
}

func buildReport(records []eatEntity) (*ReportData, error) {
	sort.Slice(records, func(i, j int) bool {
		return records[i].PayTime < records[j].PayTime
	})

	var (
		totalAmount float64
		year        = time.Unix(records[0].PayTime, 0).In(cstZone).Year()
	)

	merchantCount := map[string]int{}
	merchantAmount := map[string]float64{}
	monthAmount := map[string]float64{}
	hourCount := map[string]int{}

	var (
		first = records[0]
		max   = records[0]
	)

	// 按日期记录当天最早的一次消费
	dayEarliest := map[string]eatEntity{}

	for _, r := range records {
		t := time.Unix(r.PayTime, 0).In(cstZone)
		totalAmount += r.Amount

		merchantCount[r.Merchant]++
		merchantAmount[r.Merchant] += r.Amount

		monthKey := fmt.Sprintf("%d", int(t.Month()))
		monthAmount[monthKey] += r.Amount

		hourKey := fmt.Sprintf("%d", t.Hour())
		hourCount[hourKey]++

		dayKey := t.Format("2006-01-02")
		if prev, ok := dayEarliest[dayKey]; !ok || timeUnixLess(r.PayTime, prev.PayTime) {
			dayEarliest[dayKey] = r
		}

		if r.Amount > max.Amount {
			max = r
		}
	}

	for m := 1; m <= 12; m++ {
		key := fmt.Sprintf("%d", m)
		if _, ok := monthAmount[key]; !ok {
			monthAmount[key] = 0
		}
	}
	for h := 0; h < 24; h++ {
		key := fmt.Sprintf("%d", h)
		if _, ok := hourCount[key]; !ok {
			hourCount[key] = 0
		}
	}

	// 第一笔消费（按时间最早）
	firstTime := time.Unix(first.PayTime, 0).In(cstZone)
	firstFormatted := formatCN(firstTime)

	maxTime := time.Unix(max.PayTime, 0).In(cstZone)

	// 最常光顾
	mostFrequentLoc, mostFreqCount := maxCount(merchantCount)
	mostFrequentAmount := merchantAmount[mostFrequentLoc]

	// 消费最多的地点（按金额）
	mostSpentLoc, mostSpentAmt := maxAmount(merchantAmount)
	mostSpentCount := merchantCount[mostSpentLoc]

	// 早/午/晚餐次数
	bk, lunch, dinner := mealBuckets(records)

	// 最早的一餐（按一天中的时间）
	earliest := earliestMeal(dayEarliest)
	earliestTime := time.Unix(earliest.PayTime, 0).In(cstZone)

	// 月度消费最高
	peakMonth, peakAmount := maxAmount(monthAmount)

	chart := chartData{
		MerchantAmount:   merchantAmount,
		MonthlyAmount:    monthAmount,
		TimeDistribution: hourCount,
	}
	reportJSON, _ := json.Marshal(chart)

	return &ReportData{
		Year:                 year,
		TotalAmount:          totalAmount,
		FirstMealLocation:    first.Merchant,
		FirstMealTime:        firstFormatted,
		FirstMealAmount:      first.Amount,
		MaxMealLocation:      max.Merchant,
		MaxMealTime:          formatCN(maxTime),
		MaxMealAmount:        max.Amount,
		MostFrequentLocation: mostFrequentLoc,
		MostFrequentCount:    mostFreqCount,
		MostFrequentAmount:   mostFrequentAmount,
		MostSpentLocation:    mostSpentLoc,
		MostSpentAmount:      mostSpentAmt,
		MostSpentCount:       mostSpentCount,
		BreakfastCount:       bk,
		LunchCount:           lunch,
		DinnerCount:          dinner,
		EarliestMealLocation: earliest.Merchant,
		EarliestMealTime:     formatCN(earliestTime),
		EarliestMealAmount:   earliest.Amount,
		PeakMonth:            toInt(peakMonth),
		PeakMonthAmount:      peakAmount,
		ReportJSON:           template.JS(string(reportJSON)),
		MerchantAmount:       merchantAmount,
		MonthlyAmount:        monthAmount,
		TimeDistribution:     hourCount,
	}, nil
}

func formatCN(t time.Time) string {
	return t.Format("1月2日15时04分")
}

func maxCount(m map[string]int) (key string, count int) {
	for k, v := range m {
		if v > count {
			key, count = k, v
		}
	}
	return
}

func maxAmount(m map[string]float64) (key string, amount float64) {
	for k, v := range m {
		if v > amount {
			key, amount = k, v
		}
	}
	return
}

func mealBuckets(records []eatEntity) (breakfast, lunch, dinner int) {
	for _, r := range records {
		h := time.Unix(r.PayTime, 0).In(cstZone).Hour()
		switch {
		case h >= 6 && h < 9:
			breakfast++
		case h >= 11 && h < 14:
			lunch++
		case h >= 17 && h < 19:
			dinner++
		}
	}
	return
}

func earliestMeal(dayEarliest map[string]eatEntity) eatEntity {
	var (
		earliest eatEntity
		set      bool
	)
	for _, r := range dayEarliest {
		t := time.Unix(r.PayTime, 0).In(cstZone)
		seconds := t.Hour()*3600 + t.Minute()*60 + t.Second()
		if !set {
			earliest = r
			set = true
			continue
		}
		prev := time.Unix(earliest.PayTime, 0).In(cstZone)
		prevSeconds := prev.Hour()*3600 + prev.Minute()*60 + prev.Second()
		if seconds < prevSeconds {
			earliest = r
		} else if seconds == prevSeconds && r.PayTime < earliest.PayTime {
			earliest = r
		}
	}
	return earliest
}

func timeUnixLess(a, b int64) bool {
	return a < b
}

func toInt(s string) int {
	i, _ := strconv.Atoi(s)
	return i
}

func normalizeMerchant(name string) string {
	if plateRegex.MatchString(strings.TrimSpace(name)) {
		return "班车"
	}
	return name
}

func stringsJoin(arr []string, sep string) string {
	if len(arr) == 0 {
		return ""
	}
	res := arr[0]
	for i := 1; i < len(arr); i++ {
		res += sep + arr[i]
	}
	return res
}
