package main

import (
	"fmt"
	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/app"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/widget"
	"github.com/jlaffaye/ftp"
	"io"
	"strings"
)

var (
	client   *ftp.ServerConn
	fileList *widget.List
	output   *widget.Label
	selected string
)

func showEditWindow(a fyne.App, action, content string) {
	editWindow := a.NewWindow(fmt.Sprintf("%s File", action))
	editWindow.Resize(fyne.NewSize(400, 300))

	fileNameEntry := widget.NewEntry()
	fileNameEntry.SetPlaceHolder("File name")
	if action == "Update" {
		fileNameEntry.SetText(selected)
		fileNameEntry.Disable()
	}

	contentEntry := widget.NewMultiLineEntry()
	contentEntry.SetText(content)

	saveBtn := widget.NewButton("Save", func() {
		fileName := fileNameEntry.Text
		if fileName == "" {
			output.SetText("Specify file name")
			return
		}
		data := strings.NewReader(contentEntry.Text)
		err := client.Stor(fileName, data)
		if err != nil {
			output.SetText(fmt.Sprintf("Error saving file: %v", err))
			return
		}

		entries, _ := client.List("")
		files := []string{}
		for _, entry := range entries {
			files = append(files, entry.Name)
		}
		fileList.Refresh()
		output.SetText(fmt.Sprintf("File %s is saved", fileName))
		editWindow.Close()
	})

	cancelBtn := widget.NewButton("Cancel", func() { editWindow.Close() })

	editContent := container.NewVBox(
		fileNameEntry,
		contentEntry,
		container.NewHBox(saveBtn, cancelBtn),
	)

	editWindow.SetContent(editContent)
	editWindow.Show()
}

func main() {
	myApp := app.New()
	mainWindow := myApp.NewWindow("FTP Client")
	mainWindow.Resize(fyne.NewSize(800, 600))

	serverEntry := widget.NewEntry()
	serverEntry.SetPlaceHolder("Server (e.g., localhost:21)")
	usernameEntry := widget.NewEntry()
	usernameEntry.SetPlaceHolder("Username")
	passwordEntry := widget.NewPasswordEntry()
	passwordEntry.SetPlaceHolder("Password")
	output = widget.NewLabel("Results will appear here...")

	var files []string
	fileList = widget.NewList(
		func() int { return len(files) },
		func() fyne.CanvasObject { return widget.NewLabel("template") },
		func(i widget.ListItemID, o fyne.CanvasObject) {
			o.(*widget.Label).SetText(files[i])
		},
	)
	fileList.OnSelected = func(id widget.ListItemID) {
		selected = files[id]
	}
	fileList.Resize(fyne.NewSize(300, 400))

	connectBtn := widget.NewButton("Connect", func() {
		addr := serverEntry.Text
		username := usernameEntry.Text
		password := passwordEntry.Text

		var err error
		client, err = ftp.Dial(addr)
		if err != nil {
			output.SetText(fmt.Sprintf("Connection error: %v", err))
			return
		}

		err = client.Login(username, password)
		if err != nil {
			output.SetText(fmt.Sprintf("Authorization error: %v", err))
			return
		}

		entries, err := client.List("")
		if err != nil {
			output.SetText(fmt.Sprintf("Error while getting list: %v", err))
			return
		}

		files = nil
		for _, entry := range entries {
			files = append(files, entry.Name)
		}
		fileList.Refresh()
		output.SetText("Connection successful. File list is updated.")
	})
	createBtn := widget.NewButton("Create", func() { showEditWindow(myApp, "Create", "") })
	retrieveBtn := widget.NewButton("Retrieve", func() {
		if selected == "" {
			output.SetText("Error file for downloading")
			return
		}
		data, err := client.Retr(selected)
		if err != nil {
			output.SetText(fmt.Sprintf("Error reading file: %v", err))
			return
		}
		defer data.Close()
		content := new(strings.Builder)
		_, err = io.Copy(content, data)
		if err != nil {
			output.SetText(fmt.Sprintf("Error reading file: %v", err))
			return
		}
		output.SetText(fmt.Sprintf("Content of file %s:\n%s", selected, content.String()))
	})
	updateBtn := widget.NewButton("Update", func() {
		if selected == "" {
			output.SetText("Select file for usage")
			return
		}
		data, err := client.Retr(selected)
		if err != nil {
			output.SetText(fmt.Sprintf("Error downloading file: %v", err))
			return
		}
		defer data.Close()
		content := new(strings.Builder)
		_, err = io.Copy(content, data)
		if err != nil {
			output.SetText(fmt.Sprintf("Error reading file: %v", err))
			return
		}
		showEditWindow(myApp, "Update", content.String())
	})
	deleteBtn := widget.NewButton("Delete", func() {
		if selected == "" {
			output.SetText("Select file to delete")
			return
		}
		err := client.Delete(selected)
		if err != nil {
			output.SetText(fmt.Sprintf("Error while deleting file: %v", err))
			return
		}
		entries, _ := client.List("")
		files = nil
		for _, entry := range entries {
			files = append(files, entry.Name)
		}
		fileList.Refresh()
		output.SetText(fmt.Sprintf("File %s is deleted", selected))
	})

	top := container.NewVBox(
		widget.NewLabel("FTP Client"),
		serverEntry,
		usernameEntry,
		passwordEntry,
		connectBtn,
	)

	bottom := container.NewVBox(
		container.NewHBox(createBtn, retrieveBtn, updateBtn, deleteBtn),
		output,
	)

	split := container.NewVSplit(
		container.NewMax(fileList),
		bottom,
	)
	split.Offset = 0.7

	content := container.NewVBox(
		top,
		split,
	)

	mainWindow.SetContent(content)
	mainWindow.ShowAndRun()
}
