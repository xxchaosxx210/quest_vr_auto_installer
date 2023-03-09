import webbrowser
import os

import lib.config


STYLE = """<style>
        *,
        *::before,
        *::after {
            box-sizing: border-box;
        }

        body {
            font-family: 'Puritan', sans-serif;
            background-color: #F5F6F7;
            color: #1C1E21;
            padding: 1em;
        }

        h1 {
            font-size: 24pt;
            text-align: center;
            margin-bottom: 2rem;
        }

        h2 {
            font-size: 16pt;
            margin-top: 2rem;
        }

        p {
            font-size: 12pt;
            line-height: 1.5;
            margin-bottom: 1em;
        }

        a {
            color: #9a03d6;
            text-decoration: none;
            font-size: 12pt;
        }

        code {
            font-family: monospace;
            background-color: #F5F5F5;
            padding: 5px;
        }

        pre {
            font-family: monospace;
            background-color: #F5F5F5;
            padding: 1rem;
            white-space: pre-wrap;
        }

        li {
            font-size: 12pt;
            line-height: 1;
            margin-bottom: 2em;
        }

        .container {
            max-width: 800px;
            margin: auto;
        }

        .alert {
            background-color: #FFDDDD;
            color: #721C24;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
        }

        .code {
            background-color: #F5F5F5;
            padding: 20px;
            white-space: pre-wrap;
            margin-bottom: 20px;
        }
    </style>"""

HTML = f"""<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <title>{lib.config.APP_NAME} Help</title>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Puritan&display=swap">
    {STYLE}
</head>

<body>
    <div class="container">
        <h1>{lib.config.APP_NAME} Help</h1>

        <p>Version {lib.config.APP_VERSION}</p>
        <p>Developed by the Lone Taxi driver aka {lib.config.AUTHOR}</p>

        <hr>

        <h2>Description:</h2>
        <p>QuestCave Downloads and Installs Quest 2 Games (Paid/Free) to a Meta Quest 2 device.</p>

        <h2>What you need:</h2>
        <ol>
            <li>A Windows based PC/Laptop</li>
            <li>USB C Cable</li>
            <li>Quest 2 VR Headset with developer mode enabled (see how to setup Quest 2 Device below)</li>
            <li>Meta Oculus App installed on Mobile phone</li>
        </ol>

        <h3>Setup Quest 2 VR Headset:</h3>

        <p>In order for QuestCave to detect your Quest VR Device, you will need to take a few steps
            if you have not already, so here we go...</p>

        <ol>
            <li>
                <p>Go to the Meta Developer website and either login or create a new Account. It is basically
                    your Facebook account. The link is provided below...</p>
                <a href="https://dashboard.oculus.com/" target="_blank">https://dashboard.oculus.com/</a>
            </li>
            <li>
                <p>Now create a new Organization. Any random name will do. You're setting up a developer account
                    for testing VR Apps, but in our case its side loading Quest 2 games. Don't worry this completly
                    free!
                    and reversible if you don't want to use this feature anymore. However, you choose not to continue
                    then you
                    cannot get those great games for free.
                    Anyway, if you're feeling brave, like me then continue and agree to the terms of service</p>
            </li>
            <li>
                <p>Note: If you're a Windows user and as the time of writing this I havent built a Mac or Linux
                    version of this app so you will be a Windows user, you will need to download and install
                    an extra windows driver so Windows can recognize the Quest 2 device. I have provided the link
                    below for you...</p>
                <a
                    href="https://developer.oculus.com/downloads/package/oculus-adb-drivers/" target="_blank">https://developer.oculus.com/downloads/package/oculus-adb-drivers/</a>

                <p>Download, Install and reboot the computer.</p>
            </li>
            <li>
                <p>As a Quest 2 user, you should already have the Oculus app installed on your mobile device. Turn on
                    your
                    Quest if it isn't already, open the Oculus app on you phone, go to 'Menu' section on the bottom
                    right hand side,
                    go to 'Settings'.</p>

                <p>Make sure your headset is marked as 'Connected' within the app, head into 'Developer Mode',
                    then simply toggle it on. Reboot your Quest now.</p>
            </li>
            <li>
                <p>You're at the home stretch! Plug your freshly rebooted Quest into your computer/Android device using
                    a USB
                    Type-C cable.Now physically put on your headset, and you should see a window (in VR) that says
                    'Allow USB debugging?'
                    at which point you simply click the check box 'Always allow from this computer'.</p>

                <p>Now you're all set!</p>
            </li>
        </ol>

        <h3>How to use:</h3>

        <p>Download and Install the QuestCave app </p>
        <a href="https://questcave.com/get-the-app">https://questcave.com/get-the-app</a>

        <p>run it, Windows Firewall will ask that Deluge wants to connect to the internet
            allow it. This is perfectly fine as Deluge is a Bittorrent client and downloads
            the Games in the background.</p>

        <p>You should now be presented with a Device selection Dialog. Plugin your Quest 2 device
            via USB. Turn the VR headset on if it isnt already and Allow the PC to connect to the device
            take the Headset off and you should now see a device listed in the device selection
            dialog box of the QuestCave app. Double click on it.</p>

        <p>
            Well done, your device selected and you're ready to play some games. Simply select a Game
            in the list, right click on the mouse and select download and install. Let the download and install
            process run (may take a while depending on the size of the Game).
        </p>
        <p>
            Note: That currently, QuestCave doesnt support multiple Downloads yet. But will be added at a future release
            I just want to get a stable working version of this app first before adding new features
        </p>

        <p>
            When you're happy with the Games you have installed, put your headset back on
            open up your menu, in the top right screen select the option drop down menu
            and select Unknown Sources, your games will be located there
        </p>

        <p>
            take note this is an early release and will contain errors sometimes.
            A message box will appear and ask if you would like to send error information
            I would really appreciate it if you did as this helps improve the Application further
        </p>

        <p>
            Also, new Games will be added when they become availible, you will be notified. I do take requests
            send to the email below.
        </p>

        <p>
            any issues contact me at <a href="mailto:chaosad@hotmail.co.uk">chaosad@hotmail.co.uk</a>
        </p>
    </div>
</body>"""


def load() -> None:
    """checks if help.html exists, if not creates it and opens it in the default browser"""
    if not os.path.exists(lib.config.APP_DATA_PATH):
        os.makedirs(lib.config.APP_DATA_PATH)
    html_path = os.path.join(lib.config.APP_DATA_PATH, "help.html")
    if not os.path.exists(html_path):
        with open(html_path, "w") as f:
            f.write(HTML)
    webbrowser.open(html_path, new=0, autoraise=True)
