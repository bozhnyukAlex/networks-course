package main

import (
	"bufio"
	"fmt"
	"io"
	"net"
	"os"
)

func main() {
	conn, err := net.Dial("tcp", "localhost:8080")
	if err != nil {
		fmt.Println("Error connecting to server:", err)
		return
	}
	defer conn.Close()

	reader := bufio.NewReader(os.Stdin)
	fmt.Print("Enter command: ")
	command, _ := reader.ReadString('\n')

	_, err = conn.Write([]byte(command))
	if err != nil {
		fmt.Println("Error sending command:", err)
		return
	}

	responseReader := bufio.NewReader(conn)
	fmt.Println("Server response:")
	for {
		line, err := responseReader.ReadString('\n')
		if err == io.EOF {
			break
		}
		if err != nil {
			fmt.Println("Error reading response:", err)
			return
		}
		fmt.Print(line)
	}
}
