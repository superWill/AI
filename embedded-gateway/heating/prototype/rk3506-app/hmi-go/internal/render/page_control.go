package render

import (
	"fmt"
	"math"
	"strconv"
)

func pageControl(f *FB, v *View, targets map[string]int, buttons *[]Button) {
	panel(f, 16, 66, 768, 364, 14, true)
	f.Text("就地控制 · 点 −/+ 下发设定值(安全校验)", 34, 82, 1, Muted)
	for i, ctl := range Controls {
		ry := 112 + i*100
		cur := Pick(v, ctl.FB)
		fcur, curOK := cur.Float()
		tgt, has := targets[ctl.FB]
		if !has {
			tgt = ctl.Lo
			if curOK {
				tgt = int(math.RoundToEven(fcur)) // Python round() 银行家舍入
			}
		}
		f.Text(ctl.Label, 38, ry, 2, Ink)
		frac := 0.0
		if curOK {
			frac = math.Max(0.0, math.Min(1.0, (fcur-float64(ctl.Lo))/float64(ctl.Hi-ctl.Lo)))
		}
		f.RoundRect(38, ry+40, 320, 10, Track, 5, nil)
		f.RoundRect(38, ry+40, int(320*frac), 10, ctl.Col, 5, nil)
		d := 1
		if ctl.Unit == "%" {
			d = 0
		}
		f.Text(fmt.Sprintf("当前 %s%s", Fnum(cur, d), ctl.Unit), 38, ry+60, 1, Muted)
		bm := [4]int{480, ry, 64, 64}
		bp := [4]int{690, ry, 64, 64}
		f.RoundRect(bm[0], bm[1], bm[2], bm[3], Card2, 12, &Line)
		f.TextCenter("-", bm[0]+35, ry+12, 3, Muted)
		plusBG := Card2
		if ctl.Col == Green {
			plusBG = PaleGreen
		}
		borderCol := ctl.Col
		f.RoundRect(bp[0], bp[1], bp[2], bp[3], plusBG, 12, &borderCol)
		f.TextCenter("+", bp[0]+35, ry+12, 3, ctl.Col)
		f.TextCenter(strconv.Itoa(tgt), 617, ry+10, 3, Ink) // fnum(int, 0) ≡ 十进制整数
		f.TextCenter("设定 "+ctl.Unit, 617, ry+52, 1, Muted)
		*buttons = append(*buttons,
			Button{Rect: bm, FBID: ctl.FB, SP: ctl.SP, Delta: -ctl.Step, Lo: ctl.Lo, Hi: ctl.Hi},
			Button{Rect: bp, FBID: ctl.FB, SP: ctl.SP, Delta: ctl.Step, Lo: ctl.Lo, Hi: ctl.Hi})
	}
}
