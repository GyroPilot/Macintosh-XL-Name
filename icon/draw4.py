from PIL import Image, ImageDraw, ImageFont
from draw import mask, W
G={'X':["#...#",".#.#.","..#..",".#.#.","#...#"],'L':["#...","#...","#...","#...","####"],
   '1':[".#.","##.",".#.",".#.","###"],'6':[".##.","#...","###.","#..#",".##."],
   's1':[".#","##",".#",".#",".#"],'s6':["###","#..","###","#.#","###"]}
def stamp(im,x,y,keys,gap=1):
    for k in keys:
        g=G[k]
        for r,row in enumerate(g):
            for c,ch in enumerate(row):
                if ch=='#': im.putpixel((x+c,y+r),0)
        x+=len(g[0])+gap
def width(keys,gap=1): return sum(len(G[k][0]) for k in keys)+gap*(len(keys)-1)
def a1(): return Image.open('LisaXL_icon_A1.png').convert('L')
def on_screen(keys,gap=1):
    im=a1(); w=width(keys,gap); stamp(im,4+(15-w)//2,9,keys,gap); return im
def novent(im):
    d=ImageDraw.Draw(im); d.rectangle([22,7,28,11],fill=255); return im
def B3():
    im=novent(on_screen(['X','L'],2)); stamp(im,22,7,['s1','s6'],1); return im
def B4():
    im=on_screen(['1','6'],1); im=novent(im); G2=['X','L']
    # small XL in the panel: 3-wide X and L
    G['sX']=["#.#","#.#",".#.","#.#","#.#"]; G['sL']=["#..","#..","#..","#..","###"]
    stamp(im,22,7,['sX','sL'],1); return im
cands=[('A1  Approved (for comparison)',a1()),('B1  XL on the screen',on_screen(['X','L'],2)),('B2  16 on the screen',on_screen(['1','6'],1)),('B3  XL on screen, 16 on the side',B3()),('B4  16 on screen, XL on the side',B4())]
S=7; pad=22; TH=int(W*S*1.5); colw=W*S+pad
H=40+TH+14+18+int(W*4.5)+16+16
sheet=Image.new('RGB',(pad+colw*len(cands),H),(255,255,255)); dr=ImageDraw.Draw(sheet)
f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',13); fs=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
for i,(name,im) in enumerate(cands):
    x=pad+i*colw
    dr.text((x,12),name,fill=(0,0,0),font=f)
    sheet.paste(im.convert('RGB').resize((W*S,TH),Image.NEAREST),(x,40))
    dr.rectangle([x-1,39,x+W*S,40+TH],outline=(190,190,190))
    y2=40+TH+14
    dr.text((x,y2),'On your Lisa, enlarged 3x',fill=(90,90,90),font=fs)
    mk=mask(im); th=int(W*4.5)
    g=Image.new('RGB',(W*3+16,th+16),(170,170,170)); g.paste(im.convert('RGB').resize((W*3,th),Image.NEAREST),(8,8),mk.resize((W*3,th),Image.NEAREST)); sheet.paste(g,(x,y2+18))
    g=Image.new('RGB',(W+16,int(W*1.5)+16),(170,170,170)); g.paste(im.convert('RGB').resize((W,int(W*1.5)),Image.NEAREST),(8,8),mk.resize((W,int(W*1.5)),Image.NEAREST)); sheet.paste(g,(x+130,y2+18))
    dr.text((x+130,y2+18+int(W*1.5)+20),'Actual size',fill=(90,90,90),font=fs)
    im.save('r4_%s.png'%name[:2])
sheet.save('lisa_icon_candidates_4.png')
