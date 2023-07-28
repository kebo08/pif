import asyncio
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import random
from bs4 import BeautifulSoup as soup
import httpx

app = FastAPI()

messages = [
    "You are a good Boy",
    "You are a Gay",
    "You are a Bisexual",
    "You are a good Girl",
    "You are a person with one of the gender from LGBTQ+",
]

origins = [
    # "http://localhost.tiangolo.com",
    # "https://localhost.tiangolo.com",
    # "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def fetch_data(data_queue, ndata_queue, url, x):
    async with httpx.AsyncClient(verify=False) as client:
        try:
            response = await client.post(url, data={"mbstatus": "SEARCH", "htno": x}, timeout=30.0)
            response.raise_for_status()
            page_soup = soup(response.text, "html.parser")

            try:
                if page_soup.findAll("h1")[0].text == "HTTP Status 500 – Internal Server Error":
                    ndata_queue.put_nowait(x)
                    return False
                if (
                    page_soup.find("div", {"id": "main-message"})
                    .findAll("span")[0]
                    .text
                    == "Your connection was interrupted"
                ):
                    ndata_queue.put_nowait(x)
                    return False
            except:
                pass

            try:
                check = page_soup.find("table", {"id": "AutoNumber1"})
                if check is None:
                    ndata_queue.put_nowait(x)
                    return False

                if check.findAll("b")[1].text == "Personal Details":
                    container2 = page_soup.find("table", {"id": "AutoNumber4"})
                    Results1 = []
                    for i in container2.findAll("tr")[2:]:
                        Marks1 = []
                        temp = i.findAll("td")
                        Marks1.append(temp[0].text.strip())
                        Marks1.append(temp[1].text.strip())
                        Marks1.append(temp[2].text.strip())
                        Marks1.append(temp[3].text.strip())
                        Marks1.append(temp[4].text.strip())
                        Results1.append(Marks1)

                    container3 = page_soup.find("table", {"id": "AutoNumber5"})
                    Results2 = []
                    for i in container3.findAll("tr")[2:]:
                        Marks2 = []
                        Deat = i.findAll("td")
                        Marks2.append(Deat[0].text.strip())
                        Marks2.append(Deat[1].text.strip())
                        Marks2.append(Deat[2].text.strip())
                        Results2.append(Marks2)

                    for roti in sorted(Results1):
                        temp = {}
                        temp["Roll Number"] = x
                        if len(Results2[0]) == 3:
                            temp["CGPA"] = Results2[0][2]
                        temp["Sub Code"] = roti[0]
                        temp["Subject Name"] = roti[1]
                        temp["Credits"] = roti[2]
                        temp["Grade Points"] = roti[3]
                        temp["Grade Secured"] = roti[4]
                        for roties in sorted(Results2):
                            if roti[0][0] == roties[0]:
                                temp["SGPA"] = roties[1]
                                break

                        data_queue.put_nowait(temp)
                elif (
                    "The Hall Ticket Number"
                    == page_soup.find("table", {"id": "AutoNumber1"}).findAll("b")[1].text[9:31]
                ):
                    return True
                else:
                    ndata_queue.put_nowait(x)
                    return False

                return True
            except Exception as e:
                ndata_queue.put_nowait(x)
                return False

        except httpx.ConnectTimeout:
            # Retry the request with longer timeout
            try:
                response = await client.post(url, data={"mbstatus": "SEARCH", "htno": x}, timeout=60.0)
                response.raise_for_status()
                # Rest of the code remains the same...
            except httpx.ConnectTimeout:
                ndata_queue.put_nowait(x)
                return False
            except httpx.HTTPError:
                ndata_queue.put_nowait(x)
                return False
            except Exception as e:
                ndata_queue.put_nowait(x)
                return False


async def fetch_data_task(data_queue, ndata_queue, url, st, en):
    tasks = [fetch_data(data_queue, ndata_queue, url, i) for i in range(st, en + 1)]
    await asyncio.gather(*tasks)


@app.get("/")
async def sample():
    return {"message": random.choice(messages)}


@app.post("/download")
async def download_xlsx(url: str, range: str, background_tasks: BackgroundTasks):
    data_queue = asyncio.Queue()
    ndata_queue = asyncio.Queue()

    for i in range.split(","):
        r = str(i).split("-")
        x = int(r[0])
        y = int(r[1])

        if len(r) > 2:
            return {"custom_error": "Input format or range is wrong."}

        if x <= y:
            background_tasks.add_task(fetch_data_task, data_queue, ndata_queue, url, x, y)
        else:
            return {"custom_error": "Input format or range is wrong."}

    data = []
    ndata = []

    await fetch_data_task(data_queue, ndata_queue, url, x, y)

    while not data_queue.empty():
        data.append(await data_queue.get())

    while not ndata_queue.empty():
        ndata.append(await ndata_queue.get())

    return {
        "found_data": sorted(data, key=lambda x: (str(x["Roll Number"]) + x["Sub Code"])),
        "not_found_data": set(ndata),
    }
