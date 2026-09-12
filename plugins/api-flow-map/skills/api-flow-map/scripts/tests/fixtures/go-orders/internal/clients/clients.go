package clients

import (
	"context"
	"net/http"
	"encoding/json"
	"bytes"

	"github.com/aws/aws-sdk-go-v2/service/sns"
)

type PaymentsClient struct{ http *http.Client; baseURL string }
type Charge struct{ ID string }

func (c *PaymentsClient) Charge(ctx context.Context, amount int, token string) (*Charge, error) {
	body, _ := json.Marshal(map[string]any{"amount": amount, "token": token})
	resp, err := c.http.Post(c.baseURL+"/v2/charges", "application/json", bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	var ch Charge
	json.NewDecoder(resp.Body).Decode(&ch)
	return &ch, nil
}

func (c *PaymentsClient) Refund(ctx context.Context, paymentID string) error {
	_, err := c.http.Post(c.baseURL+"/v2/charges/"+paymentID+"/refund", "application/json", nil)
	return err
}

type InventoryClient struct{ http *http.Client; baseURL string }
type Reservation struct{ OK bool }

func (c *InventoryClient) Reserve(ctx context.Context, items any) (*Reservation, error) {
	resp, err := c.http.Post(c.baseURL+"/reservations", "application/json", nil)
	if err != nil {
		return nil, err
	}
	var r Reservation
	json.NewDecoder(resp.Body).Decode(&r)
	return &r, nil
}

func (c *InventoryClient) Release(ctx context.Context, items any) {
	req, _ := http.NewRequest(http.MethodDelete, c.baseURL+"/reservations", nil)
	c.http.Do(req)
}

type EventPublisher struct{ sns *sns.Client; topicArn string }

func (p *EventPublisher) Publish(ctx context.Context, topic, eventType, id string) {
	p.sns.Publish(ctx, &sns.PublishInput{TopicArn: &p.topicArn})
}

type FeatureFlags interface{ Enabled(name string) bool }
