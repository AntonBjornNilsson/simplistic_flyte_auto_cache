Very simplistic implementation of "auto-cache" in flyte tasks

Any task that uses @override_task will do the following, in order
 - Find out which file the task is written in
 - Recusivly find all files that file will import
 - Add all of the found files to a tar file
 - Run a md5 checksum on said tar file
 - Set the cache_version in flyte native @task to the md5 that was generated
