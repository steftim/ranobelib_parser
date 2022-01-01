import asyncio
import sys
import os
import shutil
import pyppeteer
from pyppeteer import launch
import urllib
import base64
import math
import random
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem


async def main():
    baseurl = "https://staticlib.me"
    nextchapthref = str("")


    #from https://github.com/Hell13Cat/WPD/blob/master/fb2_create.py
    def templ_char():
        return '''<section><title><p>{title}</p></title>
    {text}</section>'''

    def templ_bin():
        return '''<binary id="{name}" content-type="image/jpeg">{base}</binary>'''

    def templ():
        return '''<?xml version="1.0" encoding="utf-8"?> 
    <FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0" xmlns:l="http://www.w3.org/1999/xlink">
    <description>
    <title-info>
    <author>
    <last-name>{nickname}</last-name>
    </author>
    <book-title>{title}</book-title>
    <annotation>
    <p>{annotation}</p><p>Downloaded with RanobeLib Parser</p>
    </annotation>
    <coverpage>
    <image l:href="#cover.jpg"/></coverpage>
    </title-info>
    <document-info>
    <program-used>RanobeLib Parser</program-used>
    </document-info>
    </description>
    <body>
    {characters}
    </body>
    <binary id="cover.jpg" content-type="image/jpeg">{cover}</binary>
    {binaries}
    </FictionBook>'''
    #from https://github.com/Hell13Cat/WPD/blob/master/fb2_create.py

    def templ_img():
        return '''<p><image l:href="#{name}"/></p>'''


    def parser(content):
        textf = "<div class=\"reader-container container container_center\">"
        pos1 = content.find(textf)
        pos2 = content.find("</div>", pos1 + len(textf))
        text = content[pos1+len(textf):pos2]
        return text


    url = input("Enter url: ")
    vol = int(input("Volume: "))
    stchpt = int(input("Start chapter: "))
    #endchpt = int(input("End chapter: "))
    isPics = True
    if(input("Download pictures in text? [Y/n]: ") == 'n'):
        isPics = False

    while(True):
        filename = input("Output filename (without file extension): ")
        filename += ".fb2"


        if(os.path.exists(filename) == True):
            isOverwrite = input("File exists, overwrite? [N/y] ")
            if(isOverwrite == "y"):
                file = open(filename, "w", encoding="utf-8")
                break
            else:
                continue
        else:
            file = open(filename, "w", encoding="utf-8")
            break

    if(url.find("?bid=") != -1):
        bid = int(url[(url.find("?bid=")+5):url.find("&")])
    else:
        bid = -1
    urllen = 21
    if(url.find("https://") == -1):
        urllen -= 8
    bookname = url[urllen:url.find("?")]
    
    browser = await launch(headless=True, defaultViewport=False)
    context = await browser.createIncognitoBrowserContext()

    software_names = [SoftwareName.CHROME.value]
    operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]
    user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)

    page = await context.newPage()
    useragent = user_agent_rotator.get_random_user_agent()
    await page.setUserAgent(useragent)

    width = 1280 + math.floor(random.uniform(0, 1) * 250)
    height = 1024 + math.floor(random.uniform(0, 1) * 250)
    await page.setViewport({'width': width, 'height': height});

    download_path = str(os.path.realpath(__file__)).replace("\\" + os.path.basename(__file__), "") + "\pics"
    if os.path.exists(download_path) and os.path.isdir(download_path):
        shutil.rmtree(download_path)
    os.mkdir(download_path)
    cdp = await page.target.createCDPSession();
    await cdp.send('Page.setDownloadBehavior', { 'behavior': 'allow', 'downloadPath': download_path});
    #await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36")
    forurl = str("https://ranobelib.me") + str("/") + bookname + str("/")
    if(bid != -1):
        forurl += str("?bid=") + str(bid) + str("&section=chapters")
    else:
        forurl += str("?section=chapters")
    print("go to: " + forurl)
    await page.goto(forurl)
    await page.screenshot({'fullPage': 'True'})
    await asyncio.sleep(3)

    await page.evaluate(
                '''
                () => {{
                    imgdiv = document.querySelector('.media-sidebar__cover');
                    imgtag = imgdiv.querySelector('img');
                    link = document.createElement('a');
                    link.download = 'cover.jpg';
                    link.href = imgtag.src.replace('staticlib.me', 'ranobelib.me');
                    link.innerText = imgtag.src.replace('staticlib.me', 'ranobelib.me');
                    link.className = 'download_link_cover';
                    deltag = document.querySelector('.media-sidebar-actions');
                    deltag.remove();
                    imgtag.after(link);
                }}'''
                )
    await page.click('.download_link_cover')
    await asyncio.sleep(1)

    img = open(download_path + "\cover.jpg", "rb")
    bookpic = str("/9") + str(base64.b64encode(img.read())[2:-1])[2:-1]
    img.close()

    
    chapters_info = await page.content()
    picurlp = chapters_info.find("https://staticlib.me/uploads/cover")
    picurl = chapters_info[picurlp:chapters_info.find(".jpg",picurlp)+4]
    titlename = chapters_info[chapters_info.find("<div class=\"media-name__main\">") + 30:chapters_info.find("</div>")]
    authorf = "<div class=\"media-info-list__title\">Автор</div>"
    authorname = chapters_info[chapters_info.find(authorf) + len(authorf):chapters_info.find("</a>", chapters_info.find(authorf) +len(authorf))]
    authorname = authorname.replace("<div class=\"media-info-list__value\">","")
    authorname = authorname.replace(authorname[0:authorname.find("\">")+2], "")
    annotf = "<div class=\"media-description__text\">"
    annot = chapters_info[chapters_info.find(annotf) + len(annotf):chapters_info.find("</div>", chapters_info.find(annotf) + len(annotf))]
    chapters_info = chapters_info[chapters_info.find("<!-- START:Главы -->"):chapters_info.find("<!-- END:Главы -->")]
    globaltext = ""
    await page.close()

    imgbin = str("")

    chapthref = baseurl + str("/") + bookname + str("/v") + str(vol) + str("/c") + str(stchpt)
    nextchapthref = str("")
    if(bid != -1):
        chapthref += str("?bid=") + str(bid)
    
    chaptnum = stchpt

    repeats = 0

    i = stchpt
    while(repeats <= 3 or chapthref != '###END###'):
        page = await browser.newPage()

        cdp = await page.target.createCDPSession();
        await cdp.send('Page.setDownloadBehavior', { 'behavior': 'allow', 'downloadPath': download_path});

        await page.goto(chapthref)
        await page.screenshot({'fullPage': 'True'})
        pagestring = await page.content()
        if(str(pagestring).find("We are checking your browser...</span>") != -1):
            print("\nCaptha detected, trying to repeat...")
            input()
            repeats += 1
            await page.close()
            continue
        if(pagestring.find("Access denied | ranobelib.me used Cloudflare to restrict access</title>") != -1):
            print("Access denied by cloudflare, trying to repeat...")
            input()
            repeats += 1
            await page.close()
            continue
        repeats = 0
        
        booktext = parser(pagestring)

        fndstr = "<div data-media-down=\"md\" class=\"reader-header-action__title text-truncate\">"
        chaptnumpos = pagestring.find(fndstr)
        chaptnum = pagestring[chaptnumpos + len(fndstr) : pagestring.find("</div>", chaptnumpos+1)+1]
        currvol = int(chaptnum[chaptnum.find("Том")+3:chaptnum.find("Глава")-1])
        if(currvol > vol):
            break
        chaptnum = float(chaptnum[chaptnum.find("Глава")+6:-1])

        if((chaptnum - int(chaptnum)) == 0.0):
            chaptnum = int(chaptnum)

        print("Parsing chapter " + str(chaptnum))

        fndstr = "<a class=\"reader-next__btn button text-truncate button_label button_label_right\" href=\""
        
        pos = pagestring.find(fndstr)
        nextchapthref = pagestring[pos+len(fndstr) : pagestring.find("\" tabindex=", pos)]
        if(nextchapthref.find('class="reader-next__btn button text-truncate" tabindex="-1">На страницу тайтла</a>') != -1):
            nextchapthref = '###END###'
        print('nextchapthref ', nextchapthref)

        if(booktext.find("<img class=\"lazyload") != -1):
            while(True):
                pos = 0
                k = 0
                shutil.rmtree(download_path)
                os.mkdir(download_path)
                print("pictures detected in text, ", end='')
                if(isPics == True):
                    print("moving to ranobelib.me domain")
                else:
                    print("ignoring")
                pageinc = await context.newPage()
                useragent = user_agent_rotator.get_random_user_agent()
                await pageinc.setUserAgent(useragent)

                width = 1280 + math.floor(random.uniform(0, 1) * 100)
                height = 1024 + math.floor(random.uniform(0, 1) * 100)
                await pageinc.setViewport({'width': width, 'height': height});

                cdp = await pageinc.target.createCDPSession();
                await cdp.send('Page.setDownloadBehavior', { 'behavior': 'allow', 'downloadPath': download_path});
                picChapthref = chapthref.replace("staticlib.me", "ranobelib.me", 1)
                await pageinc.goto(picChapthref)
                pageincstring = await pageinc.content()
                if(pageincstring.find("We are checking your browser...</span>") != -1):
                    print("\nCaptha detected, trying to repeat...")
                    repeats += 1
                    await pageinc.close()
                    continue
                if(pageincstring.find("Access denied | ranobelib.me used Cloudflare to restrict access</title>") != -1):
                    print("Access denied by cloudflare, trying to repeat...")
                    repeats += 1
                    await pageinc.close()
                    continue
                repeats = 0
                await pageinc.screenshot({'fullPage': 'True'})
                await asyncio.sleep(0.5)
                if(isPics == True):
                    imgcol = await pageinc.evaluate(
                    '''
                    () => {{
                        imgdiv = document.querySelectorAll('.article-image');
                        for(it = 0; it < imgdiv.length; it++){
                            imgdiv[it].scrollIntoView()
                            imgtag = imgdiv[it].querySelector('.lazyload');
                            link = document.createElement('a');
                            link.download = 'img_' + it + '.jpg';
                            link.href = imgtag.src;
                            link.innerText = imgtag.src;
                            link.className = 'download_link_number_' + it;
                            imgtag.after(link);

                        }
                        return imgdiv.length
                    }}'''
                    )
                                        

                    for k in range(imgcol):
                        await pageinc.click('.download_link_number_' + str(k))
                        await asyncio.sleep(1)

                    for k in range(imgcol):
                        await pageinc.evaluate('''
                    () => {{
                        imgdiv = document.querySelectorAll('.article-image');
                        for(i = 0; i < imgdiv.length; i++){
                            link = document.querySelector('.download_link_number_' + i);
                            link.remove();
                            a = document.createElement('a');
                            a.innerText = "<image l:href=\\"#''' + str(vol) + "-" + str(chaptnum) + '''_" + i + ".jpg\\"/" + ">";
                            imgdiv[i].after(a);
                            imgdiv[i].remove();
                        }
                    }}''')
                
                    booktext = parser(await pageinc.content())

                    booktext = booktext.replace("<a>&lt;", "<")
                    booktext = booktext.replace("&gt;</a>", ">")

                    pos = 0

                    for k in range(imgcol):
                        img = open(download_path + "\img_" + str(k) + ".jpg", "rb")
                        imgbin += str(templ_bin().format(name = str(str(vol) + "-" + str(chaptnum) + "_" + str(k) + ".jpg"), base = str("/9") + str(base64.b64encode(img.read())[2:-1])[2:-1])) + "\n"
                        img.close()
                else:
                    imgcol = await pageinc.evaluate(
                    '''
                    () => {{
                        imgdiv = document.querySelectorAll('.article-image');
                        for(it = 0; it < imgdiv.length; it++){
                            imgdiv[it].scrollIntoView()
                            imgtag = imgdiv[it].querySelector('.lazyload');
                            imgtag.remove();
                        }
                        return imgdiv.length
                    }}'''
                    )

                    booktext = parser(await pageinc.content())

                    booktext = booktext.replace("<a>&lt;", "<")
                    booktext = booktext.replace("&gt;</a>", ">")
                await pageinc.close()
                break
        booktext = booktext.replace("&nbsp;", " ")

        titlenamepos = chapters_info.find("Том " + str(vol) + " Глава " + str(chaptnum) + " - ")+len("Том " + str(vol))+1
        chaptername = chapters_info[titlenamepos:chapters_info.find("</a>", titlenamepos)]
        globaltext += templ_char().format(title=chaptername, text=booktext)

        await page.close()
        chapthref = nextchapthref

    await browser.close()

    #final cleaning
    globaltext = globaltext.replace("<!-- -->", "")
    globaltext = globaltext.replace("<!-- Like -->", "")
    globaltext = globaltext.replace("</div>", "")

    print("\nSaving to file...")
    book = templ().format(nickname = authorname, title = titlename, annotation = annot, characters = globaltext, cover = str(bookpic), binaries = imgbin)
    file.write(book)
    file.close()
asyncio.get_event_loop().run_until_complete(main())

