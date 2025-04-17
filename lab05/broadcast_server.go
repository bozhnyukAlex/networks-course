package main

import (
	"fmt"
	"log"
	"net"
	"time"
)

func main() {
	broadcastAddr, err := net.ResolveUDPAddr("udp", "255.255.255.255:8080")
	if err != nil {
		log.Fatal("Error resolving address:", err)
	}

	conn, err := net.DialUDP("udp", nil, broadcastAddr)
	if err != nil {
		log.Fatal("Error while creating connection:", err)
	}
	defer conn.Close()

	for {
		currentTime := time.Now().Format(time.RFC3339)
		_, err := conn.Write([]byte(currentTime))
		if err != nil {
			log.Println("Error sending time:", err)
		} else {
			fmt.Println("Send time:", currentTime)
		}
		time.Sleep(1 * time.Second)
	}
}
