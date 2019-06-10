from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
import random
import sys, json, re, os, io, requests
from PIL import ImageGrab
from datetime import datetime


options = webdriver.ChromeOptions()
driver_path = r"../chromedriver.exe"

PROFILE_PATH = "C:\\Users\\{0}\\AppData\\Local\\Google\\Chrome\\User Data".format(os.environ.get("USERNAME"))

userdata_dir = 'UserData'
os.makedirs(userdata_dir, exist_ok=True)
options.add_argument('--user-data-dir=' + userdata_dir)


# 操作可能なChromeを立ち上げる
def make_driver():
    global driver

    driver = webdriver.Chrome(executable_path=driver_path, options=options)
    URL = "https://www.instagram.com/"
    driver.get(URL)
    driver.set_window_position(0, 0)
    driver.set_window_size(1200, 660)
    if driver.current_url != URL:
        print("既に他のChromeが開かれています。\nすべて閉じてからもう一度実行してください。")


# ファイルにあるキーワードに関連するタグやロケーションの詳細をファイルにまとめる
def output_analyze(fname):
    with open(fname, "r") as f:
        keywords = f.readlines()

    for keyword in keywords:
        driver.find_element_by_xpath('//input[@type="text"]').send_keys(keyword)
        sleep(2)

        tags = driver.find_elements_by_xpath('//a[contains(@href, "/explore/tags/")]')
        locations = driver.find_elements_by_xpath('//a[contains(@href, "/explore/locations/")]')
        with open("./info/" + keyword.rstrip("\n").lstrip("#") + "_info.txt", "w", encoding='utf-8') as f:
            f.write("Tags\n\n")
            for tag in tags:
                f.write(tag.text + "\n")
                f.write(tag.get_attribute("href") + "\n\n")
            f.write("\nLocations\n\n")
            for location in locations:
                f.write(location.text + "\n")
                f.write(location.get_attribute("href") + "\n\n")
        driver.find_element_by_xpath('//*[@id="react-root"]/section/nav/div[2]/div/div/div[2]/div[3]').click()


# ファイルにあるキーワードに関連するタグのhref要素を集める
def gather_tags(fname):
    with open(fname, "r") as f:
        keywords = f.readlines()

    taglist = []
    for keyword in keywords:
        driver.find_element_by_xpath('//input[@type="text"]').send_keys(keyword)
        sleep(2)
        tags = driver.find_elements_by_xpath('//a[contains(@href, "/explore/tags/")]')
        for tag in tags:
            taglist.append(tag.get_attribute("href"))
        driver.find_element_by_xpath('//*[@id="react-root"]/section/nav/div[2]/div/div/div[2]/div[3]').click()

    tagset = set(taglist)

    with open(fname.rstrip(".txt") + "_explored.txt", "w", encoding='utf-8') as f:
        for tag in tagset:
            f.write(tag + "\n")


# 投稿ページでいいね！した人とコメントした人のIDをいっぱい取得する
def id_get():
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@aria-label="保存する"]')))
    sleep(1)
    for i in range(20):
        liked_by = driver.find_elements_by_xpath('//button[@type="button"]/span')
        if len(liked_by) == 0:
            nexts = driver.find_elements_by_xpath('//a[text()="次へ"]')
            if len(nexts) != 0:
                nexts[0].click()
                sleep(3)
            else:
                break

        elif num_to_int(liked_by[0].text) >= 20:
            liked_by[0].click()
            break
        else:
            nexts = driver.find_elements_by_xpath('//a[text()="次へ"]')
            if len(nexts) != 0:
                nexts[0].click()
                sleep(3)
            else:
                break
    WebDriverWait(driver, 3)
    sleep(1)
    scrolls = driver.find_elements_by_xpath('//div[contains(@style, "flex-direction")]/div[11]')
    if len(scrolls) != 0:
        scroll = scrolls[0]
        actions = ActionChains(driver)
        actions.move_to_element(scroll)
        actions.perform()
        WebDriverWait(driver, 3)
        sleep(1)
    else:
        pass

    id_eles = driver.find_elements_by_xpath('//a[@title]')
    id_list = []
    for id_ele in id_eles:
        id_list.append(id_ele.get_attribute('title'))

    return sorted(set(id_list), key=id_list.index)


# idから個人ページの情報をjsonにまとめる
def user_detail(id, num=20):
    driver.get("https://www.instagram.com/{0}/?hl=ja".format(id))
    driver.set_page_load_timeout(10)

    names = driver.find_elements_by_tag_name('h1')
    if len(names) > 1:
        name = names[1].text
    else:
        name = ""
    nums = driver.find_elements_by_xpath('//ul/li/*/span')
    post = num_to_int(nums[0].text)
    byfollow = num_to_int(nums[1].text)
    follow = num_to_int(nums[2].text)
    intros = driver.find_elements_by_xpath("//main/div/div[1]/span")
    section = driver.find_elements_by_xpath("//section/div/span")
    if len(intros) > 0:
        intro = intros[0].text
    elif len(section) > 0:
        intro = section[0].text
    else:
        intro = ""

    posts_detail = {"id": id, "name": name, "post": post, "byfollow": byfollow, "follow": follow, "intro": intro, "posts": []}

    posts = driver.find_elements_by_xpath('//div[a[contains(@href, "/p/")]]')
    if len(posts) > 0:
        posts[0].click()
    else:
        with open(id + '.json', 'w') as f:
            json.dump(posts_detail, f, indent=2, ensure_ascii=False)

        return posts_detail

    for i in range(num):
        post_info = {}
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, '//time[1]')))
            sleep(0.2)
        except:
            next = driver.find_elements_by_xpath('//a[text()="次へ"]')
            if len(next) > 0:
                next[0].click()
                continue
            else:
                break

        post_info["datetime"] = driver.find_elements_by_tag_name("time")[-1].get_attribute("datetime")

        article = driver.find_elements_by_xpath('//h2/following-sibling::span')
        if len(article) > 0:
            post_info["article"] = article[0].text
        else:
            post_info["article"] = ""

        post_info["tags"] = []
        tags = driver.find_elements_by_xpath('//h2/following-sibling::span/a[contains(@href, "/explore/tags")]')
        for tag in tags:
            post_info["tags"].append(tag.text)

        movies = driver.find_elements_by_xpath('//video[@type="video/mp4"]')
        post_info["movie"] = []
        if len(movies) > 0:
            for j in range(len(movies)):
                post_info["movie"].append(movies[j].get_attribute("src"))

        sleep(0.1)
        pics = driver.find_elements_by_xpath('//div/div/div/div/img[contains(@srcset, "https")]')
        post_info["picture"] = []
        for pic in pics:
            try:
                post_info["picture"].append(pic.get_attribute("src"))
            except:
                pass

        contents_num = driver.find_elements_by_xpath('//div[contains(@class, "Yi5aA")]')
        if len(contents_num) > 0:
            post_info["contents_num"] = len(contents_num)
        else:
            post_info["contents_num"] = 1

        likes = driver.find_elements_by_xpath('//div/div/button[@type="button"]/span')
        views = driver.find_elements_by_xpath('//section/div/span[contains(text(), "再生")]/span')
        if len(likes) > 0:
            post_info["likes"] = num_to_int(likes[0].text)
            post_info["views"] = -1
        elif len(views) > 0:
            post_info["views"] = num_to_int(views[0].text)
            post_info["likes"] = -1
        elif len(driver.find_elements_by_xpath('//button[@type="button" and text()="いいね！1件"]')) > 0:
            post_info["likes"] = 1
            post_info["views"] = -1
        else:
            post_info["likes"] = 0
            post_info["views"] = -1

        posts_detail["posts"].append(post_info)

        next = driver.find_elements_by_xpath('//a[text()="次へ"]')
        if len(next) > 0:
            next[0].click()
        else:
            break

    with open("./users/" + id + '.json', 'w', encoding="utf-8") as f:
        json.dump(posts_detail, f, indent=2, ensure_ascii=False)

    return posts_detail


# 〇〇千などを数値化
def num_to_int(num):
    if "," in num:
        parts = num.split(",")
        return int(parts[0])*1000 + int(parts[1])
    elif "千" in num:
        return int(float(num.split("千")[0])*1000)
    elif "百万" in num:
        return int(float(num.split("百万")[0])*1000000)
    else:
        return int(num)


# hrefがたくさん書かれたファイルから、投稿をクローリングしてユーザー情報をjsonへ
def catch_users(fname):
    with open(fname, "r") as f:
        hrefs = f.readlines()

    for href in hrefs:
        for i in range(9):
            driver.get(href)
            driver.set_page_load_timeout(10)
            sleep(2)

            close_button = driver.find_elements_by_xpath('//span[@aria-label="閉じる"]')
            if len(close_button) > 0:
                close_button[0].click()

            posts = driver.find_elements_by_xpath('//div[div[img[contains(@alt, "画像")]]]')
            if len(posts) > 0:
                posts[i].click()
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@aria-label="保存する"]')))

                # ↓--------この間にクローリング時の処理---------↓

                ids = id_get()

                for id in ids:
                    try:
                        user_detail(id)
                    except:
                        continue

                # ↑--------この間にクローリング時の処理---------↑


#   main   #


make_driver()

# output_analyze("word.txt")

# gather_tags("word.txt")
catch_users("word_explored.txt")

driver.quit()
