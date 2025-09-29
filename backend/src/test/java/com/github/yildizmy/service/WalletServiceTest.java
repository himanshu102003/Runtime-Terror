package com.github.yildizmy.service;

import com.github.yildizmy.domain.entity.User;
import com.github.yildizmy.domain.entity.Wallet;
import com.github.yildizmy.dto.request.WalletRequest;
import com.github.yildizmy.dto.response.WalletResponse;
import com.github.yildizmy.repository.UserRepository;
import com.github.yildizmy.repository.WalletRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class WalletServiceTest {

    @InjectMocks
    private WalletService walletService;

    @Mock
    private WalletRepository walletRepository;

    @Mock
    private UserRepository userRepository;

    private User user;
    private Wallet wallet;
    private WalletRequest walletRequest;

    @BeforeEach
    void setUp() {
        user = new User();
        user.setId(1L);
        user.setUsername("testuser");

        wallet = new Wallet();
        wallet.setId(1L);
        wallet.setUser(user);
        wallet.setIban("TR1234567890123456789012345678");
        wallet.setBalance(new BigDecimal("1000.00"));
        wallet.setName("Test Wallet");

        walletRequest = new WalletRequest(
                1L,
                "TR1234567890123456789012345678",
                "Test Wallet",
                new BigDecimal("1000.00"),
                1L
        );
    }

    @Test
    void createWallet_shouldReturnWalletResponse() {
        when(userRepository.findById(1L)).thenReturn(Optional.of(user));
        when(walletRepository.save(any(Wallet.class))).thenReturn(wallet);

        WalletResponse result = walletService.createWallet(walletRequest);

        assertNotNull(result);
        assertEquals(1L, result.getId());
        assertEquals("TR1234567890123456789012345678", result.getIban());

        verify(userRepository).findById(1L);
        verify(walletRepository).save(any(Wallet.class));
    }

    @Test
    void getWalletById_shouldReturnWalletResponse() {
        when(walletRepository.findById(1L)).thenReturn(Optional.of(wallet));

        WalletResponse result = walletService.getWalletById(1L);

        assertNotNull(result);
        assertEquals(wallet.getIban(), result.getIban());

        verify(walletRepository).findById(1L);
    }

    @Test
    void updateWallet_shouldReturnUpdatedWallet() {
        WalletRequest updateRequest = new WalletRequest(
                1L,
                "TR9876543210987654321098765432",
                "Updated Wallet",
                new BigDecimal("2000.00"),
                1L
        );

        Wallet updatedWallet = new Wallet();
        updatedWallet.setId(1L);
        updatedWallet.setUser(user);
        updatedWallet.setIban("TR9876543210987654321098765432");
        updatedWallet.setName("Updated Wallet");
        updatedWallet.setBalance(new BigDecimal("2000.00"));

        when(walletRepository.findById(1L)).thenReturn(Optional.of(wallet));
        when(walletRepository.save(any(Wallet.class))).thenReturn(updatedWallet);

        WalletResponse result = walletService.updateWallet(1L, updateRequest);

        assertNotNull(result);
        assertEquals("Updated Wallet", result.getName());

        verify(walletRepository).findById(1L);
        verify(walletRepository).save(any(Wallet.class));
    }
}