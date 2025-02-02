## Welcome to the repository for the OHI/O Discord bot!

Here are instructions on how to set up the repository on your own machine. Note that these instructions assume you have a GitHub account and that you have Git installed. To create a GitHub account, click "sign up" in the top right corner of this webpage. For more info on installing Git, check out [Git's official installation guide](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) or see some of [the resources](#additional-resources) at the bottom of this README file.

### 1. Fork this repository ("repo" for short).

Near the top-right corner of this page will be a button labeled "**Fork**". Click it and follow the on-screen instructions to create a fork of this repo.

A fork is a copy of the repo under your own account. Creating a fork gives you the freedom to play around with the code, since changes won't affect the production code.

### 2. Clone the repository to your computer.

"Cloning" is the process of creating a local copy of a repo. Right now, your fork only exists in the cloud on GitHub. If you want to be able to edit the code in your fork on your PC, you need a copy of your fork on your PC.

[The GitHub Docs article on cloning a repo](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository) covers some of the different ways you can clone a repo. Most IDEs also have built-in menus for cloning a repo.

Regardless of the method you choose to use, you can get the URL for the repo by clicking the green **Code** button near the top right of this page. You would then paste the URL while following the steps outlined in the GitHub Docs article.

### 3. Download the config.ini file from the SharedFolder (in Google Drive).

TODO explain what this step means

### 4. Create a virtual environment.

TODO explain venv

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

### Closing remarks:

And that completes the setup process! You can now edit files, commit and push changes to your fork, and then open a pull request to merge your changes into the production code.

### Additional resources:

To learn more about using Git and GitHub, check out the following resources:

- [An Intro to Git and GitHub for Beginners](https://product.hubspot.com/blog/git-and-github-tutorial-for-beginners) by HubSpot. A good place to start for those with limited prior experience.
- [git - the simple guide](https://rogerdudler.github.io/git-guide/) covers some basic commands you will use very often.
- [The GitHub Docs](https://docs.github.com/en) has articles that cover everything you need to know about using GitHub.
- [The Pro Git ebook](https://git-scm.com/book/en/v2), which is completely free to access online. Has very comprehensive information about Git, but might be hard to follow for beginners.


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
