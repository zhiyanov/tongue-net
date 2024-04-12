import os

import networkx
from networkx.readwrite import write_graphml, read_graphml

import requests
import links

def wait(duration: int):
    time.sleep(duration)

class YandexScrapper:
    def __init__(self, key: str):
        self.key = key

        self.limit = 20
        self.graph = None

    def build(self, path: str | None = None) -> str:
        if path is None:
            path = "/"

        print(path)

        graph = networkx.DiGraph()
        graph.add_node(path)
        graph.nodes[path]["type"] = "dir"

        offset = 0
        while True:
            response = requests.get(
                "https://cloud-api.yandex.net/v1/disk/public/resources",
                params={
                    "public_key": self.key,
                    "path": path,
                    "limit": self.limit,
                    "offset": offset
                }
            )

            if not response.ok:
                break
            
            js = response.json()
            if len(js["_embedded"]["items"]) == 0:
                break
            
            for item in js["_embedded"]["items"]:
                path_ = item["path"]
                type_ = item["type"]

                if type_ == "file":
                    url_ = item["file"]
                    graph.add_node(path_)
                    graph.nodes[path_]["type"] = type_
                    graph.nodes[path_]["url"]  = url_
                elif type_ == "dir":
                    subgraph = self.build(path_)
                    graph = networkx.compose(graph, subgraph)
                    graph.add_edge(path, path_)
            
            offset += self.limit

        self.graph = graph
        return graph
    
    def sync(self, path: str):
        if self.graph is None:
            self.graph = self.build()

        for path_ in self.graph:
            type_ = self.graph.nodes[path_]["type"]
            extension_ = path_.split(".")[-1].lower()
            store_ = path + path_

            if os.path.exists(store_):
                continue

            if type_ == "dir":
                os.makedirs(store_)
            elif type_ == "file" and extension_ in [
                "png", "jpg", "jpeg", "bmp", "heic"]:
                url_ = self.graph.nodes[path_]["url"]

                print("Downloading:", path_)
                response = requests.get(url_)
                
                if not response.ok:
                    print("Dskip:", path_)
                    continue

                with open(store_, mode="wb") as file:
                    file.write(response.content)

if __name__ == "__main__":
    scrapper = YandexScrapper(links.PHOTOS_URL)
    # scrapper = YandexScrapper(links.MASKS_URL)
    graph = scrapper.build()
    write_graphml(graph, "../../data/pictures/graph.gml")
    scrapper.sync("../../data/pictures/")
    # write_graphml(graph, "../../data/masks/graph.gml")
    # scrapper.sync("../../data/masks/")
