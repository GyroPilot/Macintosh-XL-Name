from PIL import Image, ImageDraw, ImageFont
W=32
def new():
    im=Image.new('L',(W,W),255); return im, ImageDraw.Draw(im)
def rrect(d,x0,y0,x1,y1,r=1):
    d.rectangle([x0,y0,x1,y1],outline=0)
    for (cx,cy,sx,sy) in [(x0,y0,1,1),(x1,y0,-1,1),(x0,y1,1,-1),(x1,y1,-1,-1)]:
        d.point((cx,cy),255)
        if r==2:
            d.point((cx+sx,cy),255); d.point((cx,cy+sy),255); d.point((cx+sx,cy+sy),0)
def keys(d,x0,y0,x1,y1):
    for y in range(y0,y1+1):
        for x in range(x0,x1+1):
            if (x+y)%2==0: d.point((x,y),0)
def body(d,top,bot,menubar=False,sx1=19):
    rrect(d,1,top,30,bot)                              # case
    rrect(d,3,top+2,sx1,bot-2,r=2)                     # screen
    if menubar: d.line([5,top+4,sx1-2,top+4],fill=0)
    d.line([sx1+2,top+1,sx1+2,bot-1],fill=0)           # drive panel edge
    d.line([sx1+4,top+4,28,top+4],fill=0)              # drive slot
    d.line([sx1+6,top+5,26,top+5],fill=0)              # finger notch
    d.line([27,bot-2,28,bot-2],fill=0)                 # power button
    d.line([3,bot+1,28,bot+1],fill=0)                  # recessed base
    d.line([2,bot+2,29,bot+2],fill=0)
    d.point((2,bot+1),0); d.point((29,bot+1),0)
def keyboard(d,y,x0=3,x1=28,rows=3):
    d.line([x0,y,x1,y],fill=0); d.line([x0-1,y+rows+1,x1+1,y+rows+1],fill=0)
    d.line([x0,y,x0-1,y+rows+1],fill=0); d.line([x1,y,x1+1,y+rows+1],fill=0)
    keys(d,x0+1,y+1,x1-1,y+rows)
def A():
    im,d=new(); body(d,2,19); keyboard(d,25); return im
def B():
    im,d=new(); body(d,2,19,menubar=True); keyboard(d,25); return im
def C():
    im,d=new(); body(d,6,25,menubar=True); return im
def D():
    im,d=new(); body(d,1,17)
    keyboard(d,23,3,21)
    rrect(d,25,24,29,29); d.line([26,26,28,26],fill=0)   # mouse
    d.line([27,23,27,21],fill=0); d.point((26,20),0)      # cord
    return im
def E():   # squat, for stock Lisa pixels
    im,d=new(); body(d,7,18); keyboard(d,23,rows=2); return im
def mask(im):
    m=Image.new('L',(W+2,W+2),255); m.paste(im,(1,1))
    ImageDraw.floodfill(m,(0,0),128)
    return m.crop((1,1,W+1,W+1)).point(lambda v: 0 if v==128 else 255)   # 255 = inside
cands=[('A  Plain screen',A()),('B  Menu bar on screen',B()),('C  Lisa alone, larger',C()),('D  With mouse',D()),('E  Drawn for stock Lisa pixels',E())]
if __name__=='__main__':
    S=8; pad=22; colw=W*S+pad
    H=40+W*S+14+18+int(W*4.5)+16+20
    sheet=Image.new('RGB',(pad+colw*len(cands),H),(255,255,255)); dr=ImageDraw.Draw(sheet)
    f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15); fs=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
    for i,(name,im) in enumerate(cands):
        x=pad+i*colw
        dr.text((x,12),name,fill=(0,0,0),font=f)
        sheet.paste(im.convert('RGB').resize((W*S,W*S),Image.NEAREST),(x,40))
        dr.rectangle([x-1,39,x+W*S,40+W*S],outline=(190,190,190))
        y2=40+W*S+14
        dr.text((x,y2),'Square pixels',fill=(90,90,90),font=fs)
        dr.text((x+128,y2),'Stock Lisa pixels',fill=(90,90,90),font=fs)
        mk=mask(im)
        g=Image.new('RGB',(W*3+16,W*3+16),(170,170,170)); g.paste(im.convert('RGB').resize((W*3,W*3),Image.NEAREST),(8,8),mk.resize((W*3,W*3),Image.NEAREST)); sheet.paste(g,(x,y2+18))
        th=int(W*4.5)
        g=Image.new('RGB',(W*3+16,th+16),(170,170,170)); g.paste(im.convert('RGB').resize((W*3,th),Image.NEAREST),(8,8),mk.resize((W*3,th),Image.NEAREST)); sheet.paste(g,(x+128,y2+18))
        im.save('cand_%s.png'%name[0]); mk.save('mask_%s.png'%name[0])
    sheet.save('lisa_icon_candidates.png'); print(sheet.size)
