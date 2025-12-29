package main

import (
	"image/color"

	_ "embed"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/theme"
)

//go:embed fonts/SourceHanSansSC-Regular.otf
var sourceHanSans []byte

var sourceHanSansRes = fyne.NewStaticResource("SourceHanSansSC-Regular.otf", sourceHanSans)

// chineseTheme wraps the default theme but always uses Source Han Sans for text.
type chineseTheme struct{}

func (chineseTheme) Color(name fyne.ThemeColorName, variant fyne.ThemeVariant) color.Color {
	if name == theme.ColorNameDisabled {
		// 提高禁用状态的对比度，避免文本过浅
		return color.NRGBA{R: 60, G: 60, B: 60, A: 255}
	}
	return theme.DefaultTheme().Color(name, variant)
}

func (chineseTheme) Icon(name fyne.ThemeIconName) fyne.Resource {
	return theme.DefaultTheme().Icon(name)
}

func (chineseTheme) Size(name fyne.ThemeSizeName) float32 {
	return theme.DefaultTheme().Size(name)
}

func (chineseTheme) Font(style fyne.TextStyle) fyne.Resource {
	return sourceHanSansRes
}
