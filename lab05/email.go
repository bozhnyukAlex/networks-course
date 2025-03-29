package main

import (
	"fmt"
	"github.com/jordan-wright/email"
	"net/smtp"
	"os"
)

const (
	senderEmail    = "alex.bog182@gmail.com"
	senderPassword = "<!!!>"
	smtpHost       = "smtp.mail.ru"
	smtpPort       = "465"
)

func sendEmail(to, subject, body, format string) error {
	newEmail := email.NewEmail()
	newEmail.From = senderEmail
	newEmail.To = []string{to}
	newEmail.Subject = subject

	if format == "html" {
		newEmail.HTML = []byte(body)
	} else {
		newEmail.Text = []byte(body)
	}

	auth := smtp.PlainAuth("", senderEmail, senderPassword, smtpHost)
	return newEmail.Send(smtpHost+":"+smtpPort, auth)
}

func main() {
	if len(os.Args) < 4 {
		fmt.Println("Usage: go run main.go <to> <subject> <body> [format]")
		fmt.Println("Example: go run main.go recipient@example.com \"Тема\" \"Текст письма\" html")
		os.Exit(1)
	}

	to := os.Args[1]
	subject := os.Args[2]
	body := os.Args[3]
	format := "txt"
	if len(os.Args) > 4 {
		format = os.Args[4]
	}
	err := sendEmail(to, subject, body, format)
	if err != nil {
		fmt.Println("Error while sending mail:", err)
	} else {
		fmt.Println("Mail send successfully")
	}
}
