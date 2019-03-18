from datetime import datetime

from app.base import run_env,ENV_PROD

from_user_name = "gh_cdd1b7bafc74" #壹伴

text_template = """
<xml>
<ToUserName><![CDATA[%s]]></ToUserName>
<FromUserName><![CDATA[%s]]></FromUserName>
<CreateTime>%s</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[%s]]></Content>
</xml>"""

article_item_template = """
<item>
<Title><![CDATA[%s]]></Title>
<Description><![CDATA[%s]]></Description>
<PicUrl><![CDATA[%s]]></PicUrl>
<Url><![CDATA[%s]]></Url>
</item>
"""

article_template = """
<xml>
<ToUserName><![CDATA[%s]]></ToUserName>
<FromUserName><![CDATA[%s]]></FromUserName>
<CreateTime>%s</CreateTime>
<MsgType><![CDATA[news]]></MsgType>
<ArticleCount>%d</ArticleCount>
<Articles>%s</Articles>
</xml>
"""

image_template = """
<xml>
<ToUserName><![CDATA[%s]]></ToUserName>
<FromUserName><![CDATA[%s]]></FromUserName>
<CreateTime>%s</CreateTime>
<MsgType><![CDATA[image]]></MsgType>
<Image>
<MediaId><![CDATA[%s]]></MediaId>
</Image>
</xml>
"""

def gen_text_xml(to_user,content,from_user=None):
    if not from_user:
        from_user = from_user_name
    return text_template % (
        to_user,
        from_user,
        str(int(datetime.now().timestamp())),
        content
    )

def gen_article_xml(to_user,data_list,from_user=None):
    if not from_user:
        from_user = from_user_name
    items = ""
    for d in data_list:
        items += gen_article_item_xml(d)
    return article_template % (
        to_user,
        from_user,
        int(datetime.now().timestamp()),
        len(data_list),
        items
    )

def gen_article_item_xml(data):
    return article_item_template % (
        data["title"],
        data["description"],
        data["picurl"],
        data["url"]
    )

def gen_image_xml(to_user,media_id,from_user=None):
    if not from_user:
        from_user = from_user_name
    return image_template % (
        to_user,
        from_user,
        str(int(datetime.now().timestamp())),
        media_id
    )
