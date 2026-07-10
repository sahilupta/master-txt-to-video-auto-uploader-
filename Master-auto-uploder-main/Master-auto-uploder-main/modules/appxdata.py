"""
modules/appxdata.py - Appx platform data fetching
Reconstructed from appxdata.so analysis
"""
import asyncio
from logger import LOGGER
from master.server import HttpxClient
from master import utils

scraper = HttpxClient(verify_ssl=False)
semaphore = asyncio.Semaphore(36)

headers = {
    'User-Agent': 'okhttp/4.9.1',
    'Accept-Encoding': 'gzip',
    'client-service': 'Appx',
    'auth-key': 'appxapi',
    'source': 'website',
    'user-id': '',
    'authorization': '',
    'user_app_category': '',
    'language': 'en',
    'device_type': 'ANDROID'
}


async def check_server():
    """Check if the Appx server is reachable."""
    try:
        response = await scraper.get("https://www.google.com")
        if response.status_code == 200:
            LOGGER.info("Server check: Online")
            return True
        return False
    except Exception as e:
        LOGGER.error(f"Server check error: {e}")
        return False


async def collect_data(batch_id, api, token):
    """Collect all data (videos, PDFs) from a batch."""
    try:
        all_urls = await fetch_appx_v1(api, batch_id)
        if not all_urls:
            all_urls = await fetch_appx_v2(api, batch_id)
        return all_urls
    except Exception as e:
        LOGGER.error(f"Error collecting data: {e}")
        return []


async def fetch_appx_v1(api, batch_id):
    """Fetch data using Appx API v1 (subject/topic hierarchy)."""
    try:
        tasks = []
        all_urls = []

        # Get all subjects for the course
        subject_url = f"{api}/get/allsubjectfrmlivecourseclass?courseid={batch_id}"
        subject_resp = await scraper.get(subject_url, headers=headers)

        if subject_resp.status_code != 200:
            return []

        subjects = subject_resp.json()
        if isinstance(subjects, dict):
            subjects = subjects.get("data", [])

        for subject in subjects:
            u = subject.get("_id", subject.get("id", subject.get("subjectid", "")))
            SubjectName = subject.get("subject_name", subject.get("name", "Unknown Subject"))

            # Get topics for each subject
            topic_url = f"{api}/get/alltopicfrmlivecourseclass?courseid={batch_id}&subjectid={u}"
            topic_resp = await scraper.get(topic_url, headers=headers)

            if topic_resp.status_code != 200:
                continue

            topics = topic_resp.json()
            if isinstance(topics, dict):
                topics = topics.get("data", [])

            for Topic in topics:
                v = Topic.get("_id", Topic.get("id", Topic.get("topicid", "")))
                TopicName = Topic.get("topic_name", Topic.get("name", "Unknown Topic"))

                # Get content details for each topic
                ids_details = await fetch_details(semaphore, api, v, TopicName, SubjectName)
                all_urls.extend(ids_details)

        return all_urls
    except Exception as e:
        LOGGER.error(f"Error in fetch_appx_v1: {e}")
        return []


async def fetch_appx_v2(api, Batch_id, u=-1, TopicName=None, SubjectName=None):
    """Fetch data using Appx API v2 (folder-based structure)."""
    try:
        all_urls = []
        tasks = []

        # Use folder_contentsv2 endpoint
        content_url = f"{api}/get/folder_contentsv2?course_id={Batch_id}&start=-1"
        if u != -1:
            content_url = f"{api}/get/folder_contentsv2?course_id={Batch_id}&start={u}"

        res = await scraper.get(content_url, headers=headers)

        if res.status_code != 200:
            return []

        items = res.json()
        if isinstance(items, dict):
            items = items.get("data", [])

        for item in items:
            r = item.get("_id", item.get("id", ""))
            folder_wise_course = item.get("folder_wise_course", item.get("type", ""))

            if folder_wise_course == "FOLDER":
                # Recursively fetch folder contents
                sub_items = await fetch_appx_v2(api, Batch_id, r,
                    item.get("topic_name", TopicName),
                    item.get("subject_name", SubjectName))
                all_urls.extend(sub_items)
            elif folder_wise_course == "VIDEO":
                url = await get_video_url(api, item)
                if url:
                    all_urls.append({
                        "url": url,
                        "name": item.get("topic_name", item.get("name", "")),
                        "type": "video",
                        "topicName": TopicName if TopicName else "",
                        "subjectName": SubjectName if SubjectName else "",
                        "timestamp": item.get("strtotime", item.get("createdAt", ""))
                    })
            else:
                # PDF/document
                pdf_link = item.get("file_link", item.get("url", item.get("link", "")))
                if pdf_link:
                    all_urls.append({
                        "url": pdf_link,
                        "name": item.get("topic_name", item.get("name", "")),
                        "type": "pdf",
                        "is_pdf": True,
                        "topicName": TopicName if TopicName else "",
                        "subjectName": SubjectName if SubjectName else "",
                        "timestamp": item.get("strtotime", item.get("createdAt", ""))
                    })

        return all_urls
    except Exception as e:
        LOGGER.error(f"Error in fetch_appx_v2: {e}")
        return []


async def fetch_details(semaphore, api, i, topicName=None, subjectName=None):
    """Fetch content details for a specific topic."""
    async with semaphore:
        try:
            all_data = []

            # Use v3 API endpoint
            content_url = f"{api}/get/livecourseclassbycoursesubtopconceptapiv3?courseid={i}"
            res = await scraper.get(content_url, headers=headers)

            if res.status_code != 200:
                return []

            items = res.json()
            if isinstance(items, dict):
                items = items.get("data", [])

            for j in items:
                MTYPE = j.get("contentType", j.get("type", j.get("folder_wise_course", "")))
                name = j.get("topic_name", j.get("name", j.get("title", "")))

                if MTYPE in ["video", "Video", "VIDEO"]:
                    video_url = await get_video_url(api, j)
                    if video_url:
                        all_data.append({
                            "url": video_url,
                            "name": name,
                            "type": "video",
                            "topicName": topicName if topicName else "",
                            "subjectName": subjectName if subjectName else "",
                            "timestamp": j.get("strtotime", j.get("createdAt", j.get("startDate", "")))
                        })
                else:
                    # PDF/document handling
                    pdf_key = None
                    for key in ["file_link", "fileUrl", "url", "link"]:
                        if key in j:
                            pdf_key = key
                            break

                    if pdf_key:
                        pdf_link = j.get(pdf_key, "")

                        # Check for encrypted links
                        if pdf_link and j.get("_encrypted", False):
                            try:
                                xx = await utils.decrypt_link(pdf_link)
                                if xx:
                                    pdf_link = xx
                            except:
                                pass

                        if pdf_link:
                            pdf_version = j.get("_encryption_version", j.get("pdf_version", "v1"))
                            all_data.append({
                                "url": pdf_link,
                                "name": name,
                                "type": "pdf",
                                "is_pdf": True,
                                "topicName": topicName if topicName else "",
                                "subjectName": subjectName if subjectName else "",
                                "timestamp": j.get("strtotime", j.get("createdAt", j.get("startDate", "")))
                            })

            return all_data
        except Exception as e:
            LOGGER.error(f"Error in fetch_details: {e}")
            return []


async def get_video_url(api, i):
    """Get the actual video URL from content item or ID."""
    try:
        # i can be a dict (item) or a string (id)
        if isinstance(i, dict):
            video_id = i.get("video_id", i.get("_id", i.get("id", "")))
        else:
            video_id = i

        querystring = {"id": video_id}
        video_url = f"{api}/get/fetchVideoDetailsById"
        res = await scraper.get(video_url, headers=headers, params=querystring)

        if res.status_code != 200:
            return None

        data = res.json()
        if isinstance(data, dict):
            data = data.get("data", data)

        # Check for YouTube video
        enc_link = data.get("videoUrl", data.get("url", data.get("link", "")))

        if not enc_link:
            LOGGER.warning(f"Not Found Any Link For This Video: {video_id}")
            return None

        # Check if YouTube link
        if "https://youtu.be/" in str(enc_link) or "youtube.com" in str(enc_link):
            return enc_link

        # Check for encrypted links
        encrypted_links = data.get("encrypted_links", data.get("download_links", {}))
        if encrypted_links:
            # Try to get the best quality encrypted link
            enc_key = data.get("_encryption_key", data.get("key", ""))
            if enc_key:
                try:
                    dec_link = await utils.decrypt_link(enc_link)
                    if dec_link:
                        return dec_link
                except:
                    pass

        # Try keylink format
        keylink = data.get("keyLink", data.get("videoDetails", {}).get("url", ""))
        if keylink:
            return keylink

        # Try direct APPX_V format
        if "APPX_V=" in str(enc_link):
            return enc_link

        # Fallback: try to decrypt
        try:
            key = data.get("_encryption_key", data.get("key", ""))
            if key:
                dec_link = await utils.decrypt_link(enc_link)
                return dec_link
        except:
            pass

        return enc_link
    except Exception as e:
        LOGGER.error(f"Error in get_video_url: {e}")
        return None
