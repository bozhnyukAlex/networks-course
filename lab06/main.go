package main

import (
	"bufio"
	"flag"
	"fmt"
	"io"
	"net"
	"os"
	"strconv"
	"strings"
)

var server string
var username string
var password string
var command string

func connectFTP(server, username, password string) (net.Conn, error) {
	conn, err := net.Dial("tcp", server+":21")
	if err != nil {
		return nil, fmt.Errorf("connection error: %v", err)
	}
	reader := bufio.NewReader(conn)
	writer := bufio.NewWriter(conn)

	_, _, err = readResponse(reader)
	if err != nil {
		return nil, err
	}

	_, err = writer.WriteString("USER " + username + "\r\n")
	if err != nil {
		return nil, err
	}
	writer.Flush()
	code, _, err := readResponse(reader)
	if err != nil {
		return nil, err
	}
	if code != 331 {
		return nil, fmt.Errorf("unexpected answer code: %d", code)
	}

	_, err = writer.WriteString("PASS " + password + "\r\n")
	if err != nil {
		return nil, err
	}
	writer.Flush()
	code, _, err = readResponse(reader)
	if err != nil {
		return nil, err
	}
	if code != 230 {
		return nil, fmt.Errorf("authorization error: %d", code)
	}

	return conn, nil
}

func readResponse(reader *bufio.Reader) (int, string, error) {
	line, err := reader.ReadString('\n')
	if err != nil {
		return 0, "", err
	}
	line = strings.TrimRight(line, "\r\n")
	if len(line) < 3 {
		return 0, "", fmt.Errorf("wrong answer: %s", line)
	}
	code, err := strconv.Atoi(line[:3])
	if err != nil {
		return 0, "", err
	}
	if line[3] == ' ' {
		return code, line[4:], nil
	}
	var message strings.Builder
	message.WriteString(line[4:])
	message.WriteString("\n")
	for {
		line, err := reader.ReadString('\n')
		if err != nil {
			return 0, "", err
		}
		line = strings.TrimRight(line, "\r\n")
		if strings.HasPrefix(line, fmt.Sprintf("%03d ", code)) {
			message.WriteString(line[4:])
			break
		}
		message.WriteString(line)
		message.WriteString("\n")
	}
	return code, message.String(), nil
}

func enterPassiveMode(conn net.Conn) (string, int, error) {
	writer := bufio.NewWriter(conn)
	_, err := writer.WriteString("PASV\r\n")
	if err != nil {
		return "", 0, err
	}
	writer.Flush()
	reader := bufio.NewReader(conn)
	code, msg, err := readResponse(reader)
	if err != nil {
		return "", 0, err
	}
	if code != 227 {
		return "", 0, fmt.Errorf("error entering passive mode: %d %s", code, msg)
	}
	// parsing: 227 Entering Passive Mode (h1,h2,h3,h4,p1,p2)
	start := strings.Index(msg, "(")
	end := strings.Index(msg, ")")
	if start == -1 || end == -1 {
		return "", 0, fmt.Errorf("wrong PASV answer: %s", msg)
	}
	parts := strings.Split(msg[start+1:end], ",")
	if len(parts) != 6 {
		return "", 0, fmt.Errorf("wrong PASV anser: %s", msg)
	}
	ip := strings.Join(parts[:4], ".")
	p1, _ := strconv.Atoi(parts[4])
	p2, _ := strconv.Atoi(parts[5])
	port := (p1 << 8) + p2
	return ip, port, nil
}

func listFiles(conn net.Conn) error {
	ip, port, err := enterPassiveMode(conn)
	if err != nil {
		return err
	}
	dataConn, err := net.Dial("tcp", fmt.Sprintf("%s:%d", ip, port))
	if err != nil {
		return err
	}
	defer dataConn.Close()

	writer := bufio.NewWriter(conn)
	_, err = writer.WriteString("LIST\r\n")
	if err != nil {
		return err
	}
	writer.Flush()

	reader := bufio.NewReader(conn)
	code, _, err := readResponse(reader)
	if err != nil {
		return err
	}
	if code != 150 {
		return fmt.Errorf("error reading LIST: %d", code)
	}

	dataReader := bufio.NewReader(dataConn)
	for {
		line, err := dataReader.ReadString('\n')
		if err == io.EOF {
			break
		}
		if err != nil {
			return err
		}
		fmt.Print(line)
	}

	code, _, err = readResponse(reader)
	if err != nil {
		return err
	}
	if code != 226 {
		return fmt.Errorf("LIST command was not executed: %d", code)
	}
	return nil
}

func uploadFile(conn net.Conn, localFile, remoteFile string) error {
	ip, port, err := enterPassiveMode(conn)
	if err != nil {
		return err
	}
	dataConn, err := net.Dial("tcp", fmt.Sprintf("%s:%d", ip, port))
	if err != nil {
		return err
	}
	defer dataConn.Close()

	writer := bufio.NewWriter(conn)
	_, err = writer.WriteString("STOR " + remoteFile + "\r\n")
	if err != nil {
		return err
	}
	writer.Flush()

	reader := bufio.NewReader(conn)
	code, _, err := readResponse(reader)
	if err != nil {
		return err
	}
	if code != 150 {
		return fmt.Errorf("error reading STOR: %d", code)
	}

	file, err := os.Open(localFile)
	if err != nil {
		return err
	}
	defer file.Close()

	_, err = io.Copy(dataConn, file)
	if err != nil {
		return err
	}
	dataConn.Close()

	code, _, err = readResponse(reader)
	if err != nil {
		return err
	}
	if code != 226 {
		return fmt.Errorf("STOR is not executed: %d", code)
	}
	return nil
}

func downloadFile(conn net.Conn, remoteFile, localFile string) error {
	ip, port, err := enterPassiveMode(conn)
	if err != nil {
		return err
	}
	dataConn, err := net.Dial("tcp", fmt.Sprintf("%s:%d", ip, port))
	if err != nil {
		return err
	}
	defer dataConn.Close()

	writer := bufio.NewWriter(conn)
	_, err = writer.WriteString("RETR " + remoteFile + "\r\n")
	if err != nil {
		return err
	}
	writer.Flush()

	reader := bufio.NewReader(conn)
	code, _, err := readResponse(reader)
	if err != nil {
		return err
	}
	if code != 150 {
		return fmt.Errorf("error reading RETR: %d", code)
	}

	file, err := os.Create(localFile)
	if err != nil {
		return err
	}
	defer file.Close()

	_, err = io.Copy(file, dataConn)
	if err != nil {
		return err
	}
	dataConn.Close()

	code, _, err = readResponse(reader)
	if err != nil {
		return err
	}
	if code != 226 {
		return fmt.Errorf("RETR is not executed: %d", code)
	}
	return nil
}

func main1() {
	flag.StringVar(&server, "server", "", "FTP-server address")
	flag.StringVar(&username, "user", "", "FTP user")
	flag.StringVar(&password, "pass", "", "FTP password")
	flag.StringVar(&command, "command", "", "Server Command")

	flag.Parse()
	if server == "" || username == "" || password == "" || command == "" {
		fmt.Println("Server, user name, password command are required")
		flag.Usage()
		os.Exit(1)
	}

	conn, err := connectFTP(server, username, password)
	if err != nil {
		fmt.Println("Connection error:", err)
		os.Exit(1)
	}
	defer conn.Close()

	switch command {
	case "list":
		err = listFiles(conn)
	case "upload":
		if len(flag.Args()) != 2 {
			fmt.Println("Usage: upload <local_file> <remote_file>")
			os.Exit(1)
		}
		localFile := flag.Args()[0]
		remoteFile := flag.Args()[1]
		err = uploadFile(conn, localFile, remoteFile)
	case "download":
		if len(flag.Args()) != 2 {
			fmt.Println("Usage: download <remote_file> <local_file>")
			os.Exit(1)
		}
		remoteFile := flag.Args()[0]
		localFile := flag.Args()[1]
		err = downloadFile(conn, remoteFile, localFile)
	default:
		fmt.Println("Command usage:", command)
		os.Exit(1)
	}
	if err != nil {
		fmt.Println("Error:", err)
		os.Exit(1)
	}
}
