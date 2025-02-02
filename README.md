## Welcome to the repository for the OHI/O Discord bot!

Here are instructions on how to set up the repository on your own machine. Note that these instructions assume you have a GitHub account and that you have Git installed. To create a GitHub account, click "sign up" in the top right corner of this webpage. For more info on installing Git, check out [Git's official installation guide](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) or see some of [the resources](#additional-resources) at the bottom of this README file.

### 1. Fork this repository ("repo" for short).

Near the top-right corner of this page will be a button labeled "**Fork**". Click it and follow the on-screen instructions to create a fork of this repo.

A fork is a copy of the repo under your own account. Creating a fork gives you the freedom to play around with the code, since changes won't affect the production code.

### 2. Clone the repository to your computer.

"Cloning" is the process of creating a local copy of a repo. Right now, your fork only exists in the cloud on GitHub. If you want to be able to edit the code in your fork on your PC, you need a copy of your fork on your PC.

[The GitHub Docs article on cloning a repo](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository) covers some of the different ways you can clone a repo. The following instructions will tell you how to use the command line to clone a repo, as we will be doing later steps via the command line as well.

First, you should get the URL for the repo by clicking the green **Code** button near the top right of this page.

Now you should open a terminal window. Navigate to a directory where you would like to keep the local repo. (You should pick a directory that is easy to access from the command line, i.e. a directory that is not nested too deep in your file tree.)

Lastly, use the following command
```bash
git clone <URL>
```
by replacing `<URL>` with the URL you copied earlier. (If you do not know how to paste text into the terminal you are using, you will need to look that up, as it varies depending on the terminal app you are using.)

### 3. Download the `config.ini` file from the SharedFolder (in Google Drive).

You should now have a directory on your PC that contains your local repo.

The next step is to go to the tech committee's SharedFolder in Google Drive. If you do not already have access to the SharedFolder, then go to the OHI/O Discord server and check the description for the `#tech-general` text channel. There will be a link that you can use to request access to the SharedFolder.

In the SharedFolder will be a file named `config.ini`. (You might need to check a subdirectory to find the file.) You must download this file **to the root directory of your local repo**, which you cloned in step 2.

<ins>**IMPORTANT:** The `config.ini` file has some sensitive information in it. Do **NOT** share the file with anyone outside of the organization!</ins>

### 4. Create a virtual environment.

In a terminal window, navigate to the root directory of your local repo. (This is where your `config.ini` file should be after step 3.)

You should now run the following command
```bash
python -m venv venv
```
to create a virtual environment in your local repo.

[The venv article in the Python docs](https://docs.python.org/3/library/venv.html) contains some information that you might find useful for steps 4-6.

### 5. Activate the venv.

TODO explain the different commands for Windows and Mac

### 6. Download dependencies/libraries.

TODO pip install -r requirements.txt

### 7. Try running the bot.

You should now be able to try running the bot.  In order to start the bot, you need to run the [`start.py`](start.py) script. You can do this by opening a terminal window, navigating to the directory where the repo is, and then typing the following command:
```bash
python start.py
```

Once you see that the bot has finished logging in, you can try using some slash commands in the test Discord server.

To terminate the bot, type `CTRL` + `C` in the terminal (regardless of the OS you are using).

### Additional resources:

And that completes the setup process! You can now edit files, commit and push changes to your fork, and then open a pull request to merge your changes into the production code.

To learn more about using Git and GitHub, check out the following resources:

- [An Intro to Git and GitHub for Beginners](https://product.hubspot.com/blog/git-and-github-tutorial-for-beginners) by HubSpot. A good place to start for those with limited prior experience.
- [git - the simple guide](https://rogerdudler.github.io/git-guide/) covers some basic commands you will use very often.
- [The GitHub Docs](https://docs.github.com/en) has articles that cover everything you need to know about using GitHub.
- [The Pro Git ebook](https://git-scm.com/book/en/v2), which is completely free to access online. Has very comprehensive information about Git.

To learn more about using Python, check out the following resources:
- TODO find more python resources
- [The Python docs](https://docs.python.org/3/) has comprehensive information about Python, both for the programming language itself and some common tools you will use when working with Python projects.


TODO remove old README when done

1. Update .env file
  - The .env file is a sensitive document which contains our bot's token, essentially a key to logging in; Slack DM Dylan Jian for access
2. Create virtual environment by running:
```
  python -m venv venv
```
Then, Mac:
```bash
  source venv/bin/activate
```
Windows: 
```bash
  venv\Scripts\activate
```
3. Inside your virtual environment (should say (venv) at the beginning of your terminal line), run the following line to install the dependencies.
```bash
  pip install -r requirements.txt
```
4. Finally, to start the bot, run:
```bash
  python start.py
```
Note: if commands containing ```python``` didn't work for you, try ```python3 ``` instead.

Once the bot is running, use CTRL + C to stop the bot.
