package main

import (
	"bufio"
	"fmt"
	"io"
	"io/ioutil"
	"net"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

type FTPServer struct {
	listener net.Listener
	users    map[string]string
	rootDir  string
}

func NewFTPServer(rootDir string) *FTPServer {
	absRootDir, err := filepath.Abs(rootDir)
	if err != nil {
		panic("Invalid root directory: " + err.Error())
	}
	if _, err := os.Stat(absRootDir); os.IsNotExist(err) {
		os.MkdirAll(absRootDir, 0755)
	}
	return &FTPServer{
		users: map[string]string{
			"user": "password",
		},
		rootDir: absRootDir,
	}
}

func (s *FTPServer) Start() error {
	var err error
	s.listener, err = net.Listen("tcp", ":21")
	if err != nil {
		return err
	}
	fmt.Println("FTP Server started on port 21")
	for {
		conn, err := s.listener.Accept()
		if err != nil {
			fmt.Println("Error accepting connection:", err)
			continue
		}
		go s.handleConnection(conn)
	}
}

func (s *FTPServer) getDataConn(dataAddr string, dataListener net.Listener, conn net.Conn) (net.Conn, error) {
	if dataAddr != "" {
		// Активный режим (PORT)
		return net.Dial("tcp", dataAddr)
	} else if dataListener != nil {
		// Пассивный режим (PASV)
		dataConn, err := dataListener.Accept()
		if err != nil {
			return nil, err
		}
		dataListener.Close()
		return dataConn, nil
	}
	return nil, fmt.Errorf("no data connection established")
}

func (s *FTPServer) handleConnection(conn net.Conn) {
	defer conn.Close()
	fmt.Fprintf(conn, "220 Welcome to the FTP Server\r\n")
	reader := bufio.NewReader(conn)
	currentDir := s.rootDir
	var dataListener net.Listener
	var dataAddr string
	var authenticated bool
	var username string

	for {
		line, err := reader.ReadString('\n')
		if err != nil {
			fmt.Println("Error reading from connection:", err)
			break
		}
		line = strings.TrimSpace(line)
		parts := strings.SplitN(line, " ", 2)
		cmd := strings.ToUpper(parts[0])
		var arg string
		if len(parts) > 1 {
			arg = parts[1]
		}

		switch cmd {
		case "USER":
			username = arg
			fmt.Fprintf(conn, "331 Please specify the password.\r\n")
		case "PASS":
			if password, ok := s.users[username]; ok && password == arg {
				authenticated = true
				fmt.Fprintf(conn, "230 Login successful.\r\n")
			} else {
				fmt.Fprintf(conn, "530 Login incorrect.\r\n")
			}
		case "CWD":
			if !authenticated {
				fmt.Fprintf(conn, "530 Please log in.\r\n")
				continue
			}
			newDir := filepath.Join(currentDir, arg)
			newDir, err := filepath.Abs(newDir)
			if err != nil {
				fmt.Fprintf(conn, "550 Invalid directory.\r\n")
				continue
			}
			if !strings.HasPrefix(newDir, s.rootDir) {
				fmt.Fprintf(conn, "550 Permission denied.\r\n")
				continue
			}
			if _, err := os.Stat(newDir); os.IsNotExist(err) {
				fmt.Fprintf(conn, "550 No such directory.\r\n")
			} else {
				currentDir = newDir
				fmt.Fprintf(conn, "250 Directory changed to \"%s\"\r\n", currentDir)
			}
		case "PWD":
			if !authenticated {
				fmt.Fprintf(conn, "530 Please log in.\r\n")
				continue
			}
			fmt.Fprintf(conn, "257 \"%s\"\r\n", currentDir)
		case "PORT":
			if !authenticated {
				fmt.Fprintf(conn, "530 Please log in.\r\n")
				continue
			}
			parts := strings.Split(arg, ",")
			if len(parts) != 6 {
				fmt.Fprintf(conn, "501 Syntax error in parameters.\r\n")
				continue
			}
			ip := strings.Join(parts[0:4], ".")
			p1, _ := strconv.Atoi(parts[4])
			p2, _ := strconv.Atoi(parts[5])
			port := p1*256 + p2
			dataAddr = fmt.Sprintf("%s:%d", ip, port)
			fmt.Fprintf(conn, "200 PORT command successful.\r\n")
		case "NLST":
			if !authenticated {
				fmt.Fprintf(conn, "530 Please log in.\r\n")
				continue
			}
			dataConn, err := s.getDataConn(dataAddr, dataListener, conn)
			if err != nil {
				fmt.Fprintf(conn, "425 Can't open data connection.\r\n")
				continue
			}
			defer dataConn.Close()
			files, err := ioutil.ReadDir(currentDir)
			if err != nil {
				fmt.Fprintf(conn, "550 Failed to list directory.\r\n")
				continue
			}
			fmt.Fprintf(conn, "150 Opening data connection for file list.\r\n")
			for _, file := range files {
				fmt.Fprintf(dataConn, "%s\r\n", file.Name())
			}
			dataAddr = ""
			fmt.Fprintf(conn, "226 Transfer complete.\r\n")
		case "RETR":
			if !authenticated {
				fmt.Fprintf(conn, "530 Please log in.\r\n")
				continue
			}
			filePath := filepath.Join(currentDir, arg)
			if !strings.HasPrefix(filePath, s.rootDir) {
				fmt.Fprintf(conn, "550 Permission denied.\r\n")
				continue
			}
			if _, err := os.Stat(filePath); os.IsNotExist(err) {
				fmt.Fprintf(conn, "550 File not found.\r\n")
				continue
			}
			dataConn, err := s.getDataConn(dataAddr, dataListener, conn)
			if err != nil {
				fmt.Fprintf(conn, "425 Can't open data connection.\r\n")
				continue
			}
			defer dataConn.Close()
			fmt.Fprintf(conn, "150 Opening data connection for file transfer.\r\n")
			file, err := os.Open(filePath)
			if err != nil {
				fmt.Fprintf(conn, "550 Failed to open file.\r\n")
				continue
			}
			defer file.Close()
			_, err = io.Copy(dataConn, file)
			if err != nil {
				fmt.Fprintf(conn, "426 Transfer aborted.\r\n")
				continue
			}
			dataAddr = ""
			fmt.Fprintf(conn, "226 Transfer complete.\r\n")
		case "STOR":
			if !authenticated {
				fmt.Fprintf(conn, "530 Please log in.\r\n")
				continue
			}
			filePath := filepath.Join(currentDir, arg)
			if !strings.HasPrefix(filePath, s.rootDir) {
				fmt.Fprintf(conn, "550 Permission denied.\r\n")
				continue
			}
			dataConn, err := s.getDataConn(dataAddr, dataListener, conn)
			if err != nil {
				fmt.Fprintf(conn, "425 Can't open data connection.\r\n")
				continue
			}
			defer dataConn.Close()
			fmt.Fprintf(conn, "150 Opening data connection for file upload.\r\n")
			file, err := os.Create(filePath)
			if err != nil {
				fmt.Fprintf(conn, "550 Failed to create file.\r\n")
				continue
			}
			defer file.Close()
			_, err = io.Copy(file, dataConn)
			if err != nil {
				fmt.Fprintf(conn, "426 Transfer aborted.\r\n")
				continue
			}
			dataAddr = ""
			fmt.Fprintf(conn, "226 Transfer complete.\r\n")
		case "QUIT":
			fmt.Fprintf(conn, "221 Goodbye.\r\n")
			return
		case "PASV":
			if !authenticated {
				fmt.Fprintf(conn, "530 Please log in.\r\n")
				continue
			}
			if dataListener != nil {
				dataListener.Close()
			}
			var err error
			dataListener, err = net.Listen("tcp", ":0")
			if err != nil {
				fmt.Fprintf(conn, "425 Can't open data connection.\r\n")
				continue
			}
			serverIP := conn.LocalAddr().(*net.TCPAddr).IP.String()
			dataPort := dataListener.Addr().(*net.TCPAddr).Port
			ipParts := strings.Split(serverIP, ".")
			p1 := dataPort / 256
			p2 := dataPort % 256
			fmt.Fprintf(conn, "227 Entering Passive Mode (%s,%d,%d)\r\n",
				strings.Join(ipParts, ","), p1, p2)
		case "EPSV":
			if !authenticated {
				fmt.Fprintf(conn, "530 Please log in.\r\n")
				continue
			}
			if dataListener != nil {
				dataListener.Close()
			}
			var err error
			dataListener, err = net.Listen("tcp", ":0")
			if err != nil {
				fmt.Fprintf(conn, "425 Can't open data connection.\r\n")
				continue
			}
			dataPort := dataListener.Addr().(*net.TCPAddr).Port
			fmt.Fprintf(conn, "229 Entering Extended Passive Mode (|||%d|)\r\n", dataPort)
		case "FEAT":
			fmt.Fprintf(conn, "211-Features:\r\n PASV\r\n EPSV\r\n LIST\r\n211 End\r\n")
		case "TYPE":
			if !authenticated {
				fmt.Fprintf(conn, "530 Please log in.\r\n")
				continue
			}
			if arg == "A" || arg == "I" {
				fmt.Fprintf(conn, "200 Type set to %s.\r\n", arg)
			} else {
				fmt.Fprintf(conn, "501 Invalid type.\r\n")
			}
		case "LIST":
			if !authenticated {
				fmt.Fprintf(conn, "530 Please log in.\r\n")
				continue
			}
			dataConn, err := s.getDataConn(dataAddr, dataListener, conn)
			if err != nil {
				fmt.Fprintf(conn, "425 Can't open data connection.\r\n")
				continue
			}
			defer dataConn.Close()
			files, err := ioutil.ReadDir(currentDir)
			if err != nil {
				fmt.Fprintf(conn, "550 Failed to list directory.\r\n")
				continue
			}
			fmt.Fprintf(conn, "150 Opening data connection for directory listing.\r\n")
			for _, file := range files {
				mode := file.Mode().String()
				size := file.Size()
				name := file.Name()
				modTime := file.ModTime().Format("Jan 02 15:04")
				fmt.Fprintf(dataConn, "%s %d %s %s %d %s %s\r\n",
					mode, 1, "user", "group", size, modTime, name)
			}
			dataAddr = ""
			fmt.Fprintf(conn, "226 Transfer complete.\r\n")
		default:
			fmt.Fprintf(conn, "500 Unknown command.\r\n")
		}
	}
}

func main() {
	server := NewFTPServer("./ftp_root")
	err := server.Start()
	if err != nil {
		fmt.Println("Error starting server:", err)
	}
}
