# -*- coding: utf-8 -*-

import os
import random
import smtplib
import time
from collections import Counter
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

import pandas as pd
import requests
from bs4 import BeautifulSoup

import requests
import json


def get_one_page(url):
    response = requests.get(url)
    print(response.status_code)
    while response.status_code == 403:
        time.sleep(500 + random.uniform(0, 500))
        response = requests.get(url)
        print(response.status_code)
    print(response.status_code)
    if response.status_code == 200:
        return response.text

    return None


def summarize_abstract(abstract):
    url = "https://oneapi.gptnb.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Your API TOKEN",
    }
    data = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant that summarizes scientific abstracts. Especially focus on the numbers and innovative points. Response in Chinese.",
            },
            {
                "role": "user",
                "content": f"Please summarize this abstract in several sentences: {abstract}",
            },
        ],
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return "Failed to summarize abstract."


def send_email(title, content):
    """
    login()方法用来登录SMTP服务器，sendmail()方法就是发邮件，由于可以一次发给多个人，所以传入一个list，邮件正文
    是一个str，as_string()把MIMEText对象变成str。
    """
    # 发送者邮箱
    sender = "Your Email"
    # 发送者的登陆用户名和密码
    user = "Your Email"
    password = "Your Email password"
    # 发送者邮箱的SMTP服务器地址
    smtpserver = "Your Email provider smtp server"
    # 接收者的邮箱地址
    receiver = ["Receiver's email addresses"]  # receiver can be a list
    for customer in receiver:
        msg = MIMEMultipart("alternative")

        part1 = MIMEText(content, "plain", "utf-8")
        # html = open('subject_file.html','r')
        # part2 = MIMEText(html.read(), 'html')

        msg.attach(part1)
        # msg.attach(part2)

        # 发送邮箱地址
        msg["From"] = formataddr(["Name of sender", sender])
        # 收件箱地址
        msg["To"] = formataddr(["Name of receiver", customer])
        # 主题
        msg["Subject"] = title

        server = smtplib.SMTP_SSL(
            smtpserver, 465
        )  # （缺省）默认端口是25 也可以根据服务器进行设定
        server.login(user, password)  # 登陆smtp服务器
        server.sendmail(sender, customer, msg.as_string())  # 发送邮件 ，这里有三个参数
        server.quit()


def run_daily():
    path = os.path.join(os.getcwd(), "")
    urls = [
        "https://arxiv.org/list/gr-qc/new",
        "https://arxiv.org/list/physics/new",
        "https://arxiv.org/list/astro-ph/new",
    ]
    items = []
    list_subject_split_all = []
    for url in urls:
        html = get_one_page(url)
        # print(html)
        soup = BeautifulSoup(html, features="html.parser")
        dl = soup.find_all("dl")  # get all papers
        for i in range(2):  # get main subject and cross-listed papers
            content = dl[i]
            # print(content)
            date = soup.find("h3")
            list_ids = content.find_all("a", title="Abstract")
            # print(list_ids)
            list_title = content.find_all("div", class_="list-title mathjax")
            # print(list_title)
            list_authors = content.find_all("div", class_="list-authors")
            list_subjects = content.find_all("div", class_="list-subjects")
            list_abstracts = content.find_all("p", class_="mathjax")
            list_subject_split = []
            for subjects in list_subjects:
                # print(subjects.text)
                subjects = subjects.text.split(":", maxsplit=1)[1].strip()
                subjects = subjects.replace("\n\n", "")
                subjects = subjects.replace("\n", "")
                subject_split = subjects.split("; ")
                list_subject_split.append(subject_split)
                list_subject_split_all.append(subject_split)
            for i, paper in enumerate(
                zip(
                    list_ids,
                    list_title,
                    list_authors,
                    list_subjects,
                    list_subject_split,
                    list_abstracts,
                )
            ):
                items.append(
                    [
                        paper[
                            0
                        ].text.strip(),  # 2024/5/27 there are white spaces in the starting of ids and after Title:
                        paper[1].text.replace("Title:\n          ", "Title: "),
                        paper[2].text,
                        paper[3].text,
                        paper[4],
                        paper[5].text.strip(),
                    ]
                )
                # print(items[0])

    name = ["id", "title", "authors", "subjects", "subject_split", "Abstract"]
    paper = pd.DataFrame(columns=name, data=items)
    paper.to_csv(
        path
        + "daily_arxiv/"
        + time.strftime("%Y-%m-%d")
        + "_"
        + str(len(items))
        + ".csv"
    )
    """subject split"""
    subject_all = []
    for subject_split in list_subject_split_all:
        for subject in subject_split:
            subject_all.append(subject)
    subject_cnt = Counter(subject_all)
    # print(subject_cnt)
    subject_items = []
    for subject_name, times in subject_cnt.items():
        subject_items.append([subject_name, times])
    subject_items = sorted(
        subject_items, key=lambda subject_items: subject_items[1], reverse=True
    )
    name = ["name", "times"]
    subject_file = pd.DataFrame(columns=name, data=subject_items)
    # subject_file = pd.DataFrame.from_dict(subject_cnt, orient='index')
    subject_file.to_csv(
        path + "sub_cunt/" + time.strftime("%Y-%m-%d") + "_" + str(len(items)) + ".csv"
    )
    # subject_file.to_html('subject_file.html')

    """Specify key words for different catagory."""
    # Gravitational waves
    GW = [
        "gravitational wave",
        "gravitational-wave",
        "gravitational wave background",
        "neutron star",
        "black hole",
        "LIGO",
        "Virgo",
        "LISA",
        "DECIGO",
        "B-DECIGO",
        "inspiral waveform",
        "compact binary coalescing",
        "time delay interferometry",
        "compact binary merger",
        "memory effect",
        "quasi-normal mode",
        "standard siren",
        "GWTC",
        "Galactic binary",
        "white dwarf",
        "binary inspiral",
        "inspiraling binary",
        "GW1",
        "GW2",
        "ultralight bosons",
        "axion-like-particles",
    ]

    # Pulsar Timing Array
    PTA = [
        "FAST",
        "PTA",
        "pulsar timing array",
        "pulsar",
        "pulsars",
        "nanograv",
        "IPTA",
        "international pulsar timing array",
        "EPTA",
        "european pulsar timing array",
        "PPTA",
        "Parkes Pulsar Timing Array",
        "Five-hundred-meter Aperture Spherical Telescope",
        "SKA",
        "Hellings-Downs",
        "Hellings and Downs",
        "Hellings and Downs curve",
        "HD curve",
    ]

    # Machine learning
    ML = [
        "machine learning",
        "deep learning",
        "CNN",
        "RNN",
        "data analysis",
        "neural network",
        "time series forcasting",
    ]

    ASTRO = [
        "TDE",
        "GRB",
        "FRB",
        "tidal disruption event",
        "gamma ray burst",
        "fast radio burst",
    ]

    # Select GW papaers
    GW_papers = paper[paper["title"].str.contains(GW[0], case=False)]
    # print(f"Selected papers1 title: {selected_papers1['title']}")
    for key_word in GW[1:]:
        tmp_papers = paper[paper["title"].str.contains(key_word, case=False)]
        # print(f"In field {key_word}, papers are: {tmp_papers['title']}")
        GW_papers = pd.concat([GW_papers, tmp_papers], axis=0)
    # print(f"Selected papers 1: {selected_papers1['title']}")
    GW_papers.drop_duplicates(subset="title", inplace=True)
    GW_papers.to_csv(
        path + "GW/" + time.strftime("%Y-%m-%d") + "_" + str(len(GW_papers)) + ".csv"
    )

    # Select PTA papers
    PTA_papers = paper[paper["title"].str.contains(PTA[0], case=True)]
    for key_word in PTA[1:]:
        tmp_papers = paper[paper["title"].str.contains(key_word, case=False)]
        # print(f"temp paper: {tmp_papers['title']}")
        PTA_papers = pd.concat([PTA_papers, tmp_papers], axis=0)
    # print(f"Selectedpapers 2: {selected_papers2['title']}")
    PTA_papers.drop_duplicates(subset="title", inplace=True)
    PTA_papers.to_csv(
        path + "PTA/" + time.strftime("%Y-%m-%d") + "_" + str(len(PTA_papers)) + ".csv"
    )

    # Select ML papers
    ML_papers = paper[paper["title"].str.contains(ML[0], case=False)]
    for key_word in ML[1:]:
        tmp_papers = paper[paper["title"].str.contains(key_word, case=False)]
        # print(f"temp paper: {tmp_papers['title']}")
        ML_papers = pd.concat([ML_papers, tmp_papers], axis=0)
    # print(f"Selectedpapers 2: {selected_papers2['title']}")
    ML_papers.drop_duplicates(subset="title", inplace=True)
    ML_papers.to_csv(
        path + "ML/" + time.strftime("%Y-%m-%d") + "_" + str(len(ML_papers)) + ".csv"
    )

    # Select ASTRO papaers
    ASTRO_papers = paper[paper["title"].str.contains(ASTRO[0], case=False)]
    # print(f"Selected papers1 title: {selected_papers1['title']}")
    for key_word in ASTRO[1:]:
        tmp_papers = paper[paper["title"].str.contains(key_word, case=False)]
        # print(f"In field {key_word}, papers are: {tmp_papers['title']}")
        ASTRO_papers = pd.concat([ASTRO_papers, tmp_papers], axis=0)
    # print(f"Selected papers 1: {selected_papers1['title']}")
    ASTRO_papers.drop_duplicates(subset="title", inplace=True)
    ASTRO_papers.to_csv(
        path
        + "Astro/"
        + time.strftime("%Y-%m-%d")
        + "_"
        + str(len(ASTRO_papers))
        + ".csv"
    )

    """combined"""
    selected_papers = pd.concat(
        [GW_papers, PTA_papers, ML_papers, ASTRO_papers], axis=0
    )
    selected_papers.to_csv(
        path
        + "daily_arxiv/selected_"
        + time.strftime("%Y-%m-%d")
        + "_"
        + str(len(selected_papers))
        + ".csv"
    )

    """send email"""
    # selected_papers.to_html('email.html')
    content = "Today's arxiv has {} new papers in physics area, {} are about ASTRO, {} are about GW, {} are about PTA, and {} are about ML and DL.\n\n".format(
        len(items), len(ASTRO_papers), len(GW_papers), len(PTA_papers), len(ML_papers)
    )
    content += "Ensure your ASTRO keywords is " + str(ASTRO) + "\n\n"
    content += "This is your paperlist.Enjoy! \n\n"
    for i, selected_paper4 in enumerate(
        zip(
            ASTRO_papers["id"],
            ASTRO_papers["title"],
            ASTRO_papers["authors"].to_list(),
            ASTRO_papers["subject_split"],
            ASTRO_papers["Abstract"],
        )
    ):
        # print(content1)
        content1, content2, content3, content4, abstract = selected_paper4
        summary = summarize_abstract(abstract)
        content += (
            "------------"
            + str(i + 1)
            + "------------\n"
            + content1
            + "\n"
            + content2
            + "\n"
            + content3
            + "\n"
            + str(content4)
            + "\n"
            + "GPT 摘要总结："
            + summary
            + "\n"
        )
        content1 = content1.split(":", maxsplit=1)[1]
        content += "https://arxiv.org/abs/" + content1 + "\n\n"

    content += "Ensure your GW keywords is " + str(GW) + "\n\n"
    content += "This is your paperlist.Enjoy! \n\n"
    for i, selected_paper in enumerate(
        zip(
            GW_papers["id"],
            GW_papers["title"],
            GW_papers["authors"].to_list(),
            GW_papers["subject_split"],
            GW_papers["Abstract"],
        )
    ):
        # print(content1)
        content1, content2, content3, content4, abstract = selected_paper
        summary = summarize_abstract(abstract)
        content += (
            "------------"
            + str(i + 1)
            + "------------\n"
            + content1
            + "\n"
            + content2
            + "\n"
            + "Authors: "
            + content3
            + "\n"
            + str(content4)
            + "\n"
            + "GPT 摘要总结："
            + summary
            + "\n"
        )
        content1 = content1.split(":", maxsplit=1)[1]
        content += "https://arxiv.org/abs/" + content1 + "\n\n"

    content += "Ensure your PTA keywords is " + str(PTA) + "\n\n"
    content += "This is your paperlist.Enjoy! \n\n"
    for i, selected_paper2 in enumerate(
        zip(
            PTA_papers["id"],
            PTA_papers["title"],
            PTA_papers["authors"],
            PTA_papers["subject_split"],
            PTA_papers["Abstract"],
        )
    ):
        # print(content1)
        content1, content2, content3, content4, abstract = selected_paper2
        summary = summarize_abstract(abstract)
        content += (
            "------------"
            + str(i + 1)
            + "------------\n"
            + content1
            + "\n"
            + content2
            + "\n"
            + "Authors: "
            + content3
            + "\n"
            + str(content4)
            + "\n"
            + "GPT 摘要总结："
            + summary
            + "\n"
        )
        content1 = content1.split(":", maxsplit=1)[1]
        content += "https://arxiv.org/abs/" + content1 + "\n\n"

    content += "Ensure your ML keywords is " + str(ML) + "\n\n"
    content += "This is your paperlist.Enjoy! \n\n"
    for i, selected_paper3 in enumerate(
        zip(
            ML_papers["id"],
            ML_papers["title"],
            ML_papers["authors"],
            ML_papers["subject_split"],
            ML_papers["Abstract"],
        )
    ):
        # print(content1)
        content1, content2, content3, content4, abstract = selected_paper3
        summary = summarize_abstract(abstract)
        content += (
            "------------"
            + str(i + 1)
            + "------------\n"
            + content1
            + "\n"
            + content2
            + "\n"
            + "Authors: "
            + content3
            + "\n"
            + str(content4)
            + "\n"
            + "GPT 摘要总结："
            + summary
            + "\n"
        )
        content1 = content1.split(":", maxsplit=1)[1]
        content += "https://arxiv.org/abs/" + content1 + "\n\n"

    content += "Here is the Research Direction Distribution Report. \n\n"
    for subject_name, times in subject_items:
        content += subject_name + "   " + str(times) + "\n"
    title = time.strftime("%Y-%m-%d") + " you have {}+{}+{}+{} papers".format(
        len(GW_papers), len(PTA_papers), len(ML_papers), len(ASTRO_papers)
    )
    send_email(title, content)
    freport = open(path + "report/" + title + ".txt", "w")
    freport.write(content)
    freport.close()

    # push to wechat
    """ message too large need vip
    push_token = "8935374ce77e496992cce6d226ccf567"
    topic = "2"
    push_title = title
    push_content = content
    template = "txt"
    url = f"https://www.pushplus.plus/send?token={push_token}&title={push_title}&content={push_content}&template={template}&topic={topic}"
    print(url)
    r = requests.get(url=url)
    print(r.text)
    """

    # dowdload key_word selected papers
    # list_subject_split = []
    # if not os.path.exists(path + "daily_arxiv/" + time.strftime("%Y-%m-%d")):
    #     os.makedirs(path + "daily_arxiv/" + time.strftime("%Y-%m-%d"))
    # for selected_paper_id, selected_paper_title in zip(
    #     selected_papers["id"], selected_papers["title"]
    # ):
    #     selected_paper_id = selected_paper_id.split(":", maxsplit=1)[1]
    #     selected_paper_title = selected_paper_title.split(":", maxsplit=1)[1]
    #     r = requests.get("https://arxiv.org/pdf/" + selected_paper_id)
    #     while r.status_code == 403:
    #         time.sleep(500 + random.uniform(0, 500))
    #         r = requests.get("https://arxiv.org/pdf/" + selected_paper_id)
    #     selected_paper_id = selected_paper_id.replace(".", "_")
    #     pdfname = selected_paper_title.replace("/", "_")  # pdf名中不能出现/和：
    #     pdfname = pdfname.replace("?", "_")
    #     pdfname = pdfname.replace('"', "_")
    #     pdfname = pdfname.replace("*", "_")
    #     pdfname = pdfname.replace(":", "_")
    #     pdfname = pdfname.replace("\n", "")
    #     pdfname = pdfname.replace("\r", "")
    #     print(
    #         path
    #         + "daily_arxiv/"
    #         + time.strftime("%Y-%m-%d")
    #         + "/%s %s.pdf" % (selected_paper_id, selected_paper_title)
    #     )
    #     with open(
    #         path
    #         + "daily_arxiv/"
    #         + time.strftime("%Y-%m-%d")
    #         + "/%s %s.pdf" % (selected_paper_id, pdfname),
    #         "wb",
    #     ) as code:
    #         code.write(r.content)


if __name__ == "__main__":
    run_daily()
    print("Enjoy Your Papers")
    # send_email("Test", "This is a test")
    time.sleep(1)
