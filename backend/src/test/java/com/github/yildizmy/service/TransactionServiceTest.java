package com.github.yildizmy.service;

import com.github.yildizmy.domain.entity.Transaction;
import com.github.yildizmy.domain.entity.Wallet;
import com.github.yildizmy.domain.enums.Status;
import com.github.yildizmy.dto.request.TransactionRequest;
import com.github.yildizmy.dto.response.CommandResponse;
import com.github.yildizmy.dto.mapper.TransactionResponseMapper;
import com.github.yildizmy.repository.TransactionRepository;
import com.github.yildizmy.repository.WalletRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class TransactionServiceTest {

    @InjectMocks
    private TransactionService transactionService;

    @Mock
    private TransactionRepository transactionRepository;

    @Mock
    private WalletRepository walletRepository;

    @Mock
    private TransactionResponseMapper transactionResponseMapper;

    private TransactionRequest transactionRequest;
    private Wallet fromWallet;
    private Wallet toWallet;
    private Transaction transaction;

    @BeforeEach
    void setUp() {
        fromWallet = new Wallet();
        fromWallet.setId(1L);
        fromWallet.setBalance(new BigDecimal("1000.00"));
        fromWallet.setIban("TR1234567890123456789012345678");

        toWallet = new Wallet();
        toWallet.setId(2L);
        toWallet.setBalance(new BigDecimal("500.00"));
        toWallet.setIban("TR9876543210987654321098765432");

        transactionRequest = createTransactionRequest();

        transaction = new Transaction();
        transaction.setId(1L);
        transaction.setAmount(new BigDecimal("100.00"));
        transaction.setDescription("Test transaction");
        transaction.setFromWallet(fromWallet);
        transaction.setToWallet(toWallet);
        transaction.setStatus(Status.PENDING);
    }

    @Test
    void createTransaction_shouldReturnCommandResponse() {
        when(walletRepository.findById(1L)).thenReturn(Optional.of(fromWallet));
        when(walletRepository.findById(2L)).thenReturn(Optional.of(toWallet));
        when(transactionRepository.save(any(Transaction.class))).thenReturn(transaction);

        CommandResponse result = transactionService.createTransaction(transactionRequest);

        assertNotNull(result);
        assertTrue(result.isSuccess());
        assertNotNull(result.getMessage());

        verify(walletRepository).findById(1L);
        verify(walletRepository).findById(2L);
        verify(transactionRepository).save(any(Transaction.class));
    }

    @Test
    void findAllTransactions_shouldReturnPagedResults() {
        Pageable pageable = PageRequest.of(0, 10);
        List<Transaction> transactions = List.of(transaction);
        Page<Transaction> page = new PageImpl<>(transactions, pageable, 1);

        when(transactionRepository.findAll(pageable)).thenReturn(page);

        Page<Transaction> result = transactionRepository.findAll(pageable);

        assertNotNull(result);
        assertEquals(1, result.getTotalElements());
        assertEquals(1, result.getContent().size());

        verify(transactionRepository).findAll(pageable);
    }

    private TransactionRequest createTransactionRequest() {
        var request = new TransactionRequest();
        request.setId(1L);
        request.setAmount(new BigDecimal("100.00"));
        request.setDescription("Test transaction");
        request.setTimestamp(Instant.now());
        request.setTransactionId(UUID.randomUUID());
        request.setStatus(Status.PENDING);
        request.setFromAccount("TR1234567890123456789012345678");
        request.setToAccount("TR9876543210987654321098765432");
        request.setUserId(1L);
        return request;
    }
}