from PIL import Image, ImageDraw, ImageFont
from draw import rrect, keyboard, mask, W
def base(lines, slot='notch'):
    im=Image.new('L',(W,W),255); d=ImageDraw.Draw(im); top,bot=5,18
    rrect(d,1,top,30,bot)
    rrect(d,3,top+2,19,bot-2,r=2)
    for y in lines: d.line([22,y,28,y],fill=0)         # vent lines
    if slot=='notch':
        d.line([22,bot-4,28,bot-4],fill=0); d.line([24,bot-3,26,bot-3],fill=0)
    else:                                              # slot with eject button at the right end
        d.line([22,bot-3,26,bot-3],fill=0); d.rectangle([27,bot-4,28,bot-3],fill=0)
    d.line([3,bot+1,28,bot+1],fill=0); d.line([2,bot+2,29,bot+2],fill=0)
    d.point((2,bot+1),0); d.point((29,bot+1),0); d.line([26,bot+1,27,bot+1],fill=255)
    keyboard(d,23,rows=2); return im
cands=[('A1  Two lines',base([8,10])),('A2  Three lines',base([7,9,11])),('A3  Three lines, slot with button',base([7,9,11],'button'))]
S=8; pad=22; TH=int(W*S*1.5); colw=W*S+pad
H=40+TH+14+18+int(W*4.5)+16+16
sheet=Image.new('RGB',(pad+colw*len(cands),H),(255,255,255)); dr=ImageDraw.Draw(sheet)
f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15); fs=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
for i,(name,im) in enumerate(cands):
    x=pad+i*colw
    dr.text((x,12),name,fill=(0,0,0),font=f)
    sheet.paste(im.convert('RGB').resize((W*S,TH),Image.NEAREST),(x,40))
    dr.rectangle([x-1,39,x+W*S,40+TH],outline=(190,190,190))
    y2=40+TH+14
    dr.text((x,y2),'On your Lisa (stock)',fill=(90,90,90),font=fs)
    dr.text((x+128,y2),'On a square-pixel Mac',fill=(90,90,90),font=fs)
    mk=mask(im); th=int(W*4.5)
    g=Image.new('RGB',(W*3+16,th+16),(170,170,170)); g.paste(im.convert('RGB').resize((W*3,th),Image.NEAREST),(8,8),mk.resize((W*3,th),Image.NEAREST)); sheet.paste(g,(x,y2+18))
    g=Image.new('RGB',(W*3+16,W*3+16),(170,170,170)); g.paste(im.convert('RGB').resize((W*3,W*3),Image.NEAREST),(8,8),mk.resize((W*3,W*3),Image.NEAREST)); sheet.paste(g,(x+128,y2+18))
    im.save('r3_%s.png'%name[:2]); mk.save('r3_mask_%s.png'%name[:2])
sheet.save('lisa_icon_candidates_3.png')
