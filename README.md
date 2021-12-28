                                                        ..Jai Hind..
# Army1o1
Search Engine Indian Army Hackathon

Steps to Run Army 1o1 search engine..

1.) install mustinstall.txt by pip command ==>

`sudo pip install -r mustinstall.txt`

2.) After that build the docker image by using this command. This will return the id of the new docker image we will use that in next command.

`docker build ./`

3.) Run the docker image by using this command, You can configure the port according to yourself.

`docker run -p 80:5000 id_of_docker_image`

4.) Now you can access the search engine on 127.0.0.1 on your browser.

For Stopping this docker pass this commad for getting container id.

`docker container ls`
 
 and use this id in given command to stop the container
 
 `docker stop container_id`
