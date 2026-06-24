# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont

FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
def font(b, sz): return ImageFont.truetype(FB if b else FR, sz)

# palette
BG1=(11,16,32); BG2=(16,24,52); LINE=(36,49,86)
TXT=(232,236,246); MUTED=(154,166,196)
ACCENT=(79,140,255); GREEN=(39,211,162); GOLD=(255,207,92); RED=(255,107,107)

def vgrad(w,h,c1,c2):
    base=Image.new("RGB",(w,h),c1); top=Image.new("RGB",(w,h),c2)
    mask=Image.new("L",(w,h))
    md=mask.load()
    for y in range(h):
        v=int(255*(y/h))
        for x in range(w): md[x,y]=v
    base.paste(top,(0,0),mask); return base

def rrect(d,xy,r,fill=None,outline=None,width=1):
    d.rounded_rectangle(xy,radius=r,fill=fill,outline=outline,width=width)

def center(d,text,f,cx,y,fill):
    w=d.textlength(text,font=f); d.text((cx-w/2,y),text,font=f,fill=fill)

# ---------- OG share image 1200x630 ----------
def make_og():
    W,H=1200,630
    img=vgrad(W,H,BG1,BG2); d=ImageDraw.Draw(img)
    # subtle border
    rrect(d,[8,8,W-8,H-8],24,outline=LINE,width=2)
    # brand
    rrect(d,[60,52,104,96],12,fill=ACCENT)
    d.text((68,60),"LR",font=font(1,26),fill=(255,255,255))
    d.text((120,58),"ListReady",font=font(1,34),fill=TXT)
    rrect(d,[350,62,486,98],16,fill=(18,30,68))
    d.text((366,69),"in-browser",font=font(1,18),fill=GREEN)
    # headline
    d.text((60,150),"iPhone HEIC  →  JPG",font=font(1,76),fill=TXT)
    d.text((60,238),"in seconds. Free.",font=font(1,76),fill=ACCENT)
    # subline
    d.text((62,348),"Resize for Etsy · eBay · Amazon · Poshmark · strip GPS data",font=font(0,28),fill=MUTED)
    # before / after cards
    cy=420; cw=250; ch=120
    # HEIC card (red)
    rrect(d,[62,cy,62+cw,cy+ch],18,fill=(40,20,26),outline=RED,width=2)
    center(d,"HEIC",font(1,40),62+cw/2,cy+28,RED)
    center(d,"rejected ✕",font(0,22),62+cw/2,cy+78,MUTED)
    # arrow
    d.text((332,cy+38),"→",font=font(1,60),fill=TXT)
    # JPG card (green)
    rrect(d,[430,cy,430+cw,cy+ch],18,fill=(16,40,34),outline=GREEN,width=2)
    center(d,"JPG",font(1,40),430+cw/2,cy+28,GREEN)
    center(d,"upload-ready ✓",font(0,22),430+cw/2,cy+78,MUTED)
    # right privacy badge
    rrect(d,[760,418,1140,540],18,fill=(15,22,46),outline=LINE,width=2)
    d.text((788,438),"100% private",font=font(1,30),fill=GOLD)
    d.text((788,482),"Photos never leave",font=font(0,24),fill=MUTED)
    d.text((788,512),"your device.",font=font(0,24),fill=MUTED)
    # footer url
    d.text((62,575),"officialcurtiis.github.io/listready",font=font(1,24),fill=ACCENT)
    img.save("og-image.png")
    print("wrote og-image.png", img.size)

# ---------- demo GIF ----------
def base_frame():
    W,H=900,506
    img=vgrad(W,H,BG1,BG2); d=ImageDraw.Draw(img)
    # top bar
    rrect(d,[0,0,W,64],0,fill=(13,20,40))
    rrect(d,[24,16,60,52],10,fill=ACCENT); d.text((30,22),"LR",font=font(1,22),fill=(255,255,255))
    d.text((74,20),"ListReady",font=font(1,26),fill=TXT)
    return img,d,W,H

def card(d,x,y,w,h,fill=(18,26,48)):
    rrect(d,[x,y,x+w,y+h],16,fill=fill,outline=LINE,width=2)

def make_gif():
    frames=[]
    # Frame 1: file dropped
    img,d,W,H=base_frame()
    card(d,60,110,780,150)
    d.text((90,135),"Dropped from your iPhone:",font=font(0,24),fill=MUTED)
    rrect(d,[90,180,360,230],10,fill=(40,20,26),outline=RED,width=2)
    d.text((108,192),"IMG_4821.HEIC",font=font(1,24),fill=RED)
    d.text((380,190),"✕ won't upload to Etsy",font=font(0,22),fill=MUTED)
    d.text((60,300),"1 photo ready",font=font(0,24),fill=MUTED)
    rrect(d,[60,340,300,400],14,fill=ACCENT); d.text((96,356),"Process photo",font=font(1,24),fill=(255,255,255))
    frames.append(img)
    # Frames 2-3: progress
    for pct in (35,75):
        img,d,W,H=base_frame()
        card(d,60,110,780,150)
        d.text((90,150),"Converting & resizing…  "+str(pct)+"%",font=font(1,28),fill=TXT)
        rrect(d,[90,210,810,238],14,fill=(30,40,66))
        rrect(d,[90,210,90+int(720*pct/100),238],14,fill=GREEN)
        d.text((60,320),"100% in your browser — nothing uploaded.",font=font(0,22),fill=MUTED)
        frames.append(img)
    # Frame 4: done
    img,d,W,H=base_frame()
    card(d,60,110,780,180,fill=(16,34,30))
    d.text((90,135),"Done ✓",font=font(1,34),fill=GREEN)
    rrect(d,[90,190,360,242],10,fill=(16,40,34),outline=GREEN,width=2)
    d.text((108,202),"IMG_4821.jpg",font=font(1,24),fill=GREEN)
    d.text((380,188),"−62% smaller",font=font(1,24),fill=GOLD)
    d.text((380,222),"✓ Etsy / eBay ready",font=font(0,22),fill=MUTED)
    d.text((60,330),"HEIC → JPG · resized · GPS stripped",font=font(0,24),fill=MUTED)
    d.text((60,372),"officialcurtiis.github.io/listready",font=font(1,26),fill=ACCENT)
    frames.append(img); frames.append(img)  # hold last frame
    durations=[1300,700,700,1400,1400]
    frames[0].save("demo.gif",save_all=True,append_images=frames[1:],duration=durations,loop=0,optimize=True)
    print("wrote demo.gif", len(frames),"frames")

make_og()
make_gif()
